# Copyright (C) 2025  Romolo Politi
from __future__ import annotations

from itertools import cycle
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import rich_click as click
from matplotlib.patches import Patch
from rich.console import Console
from rich_click import RichContext

from gantty.time_tools import string_to_timedelta
from importlib.metadata import version as get_version

__version__ = get_version("gantty")
_PALETTE = ("#E64646", "#E69646", "#34D05C", "#34D0C3", "#3475D0")


def buildCD(sessions) -> dict:
    color_cycle = cycle(_PALETTE)
    return {session: next(color_cycle) for session in sessions}


def _parse_after_reference(start_value: str) -> str | None:
    parts = str(start_value).strip().split(maxsplit=1)
    if len(parts) == 2 and parts[0].lower() == "after":
        return parts[1].strip()
    return None


def build(ctx: RichContext, inputFile: Path, show: bool) -> pd.DataFrame:
    original_df = pd.read_csv(inputFile)
    df = original_df.copy()
    df.columns = [col.strip().title() for col in df.columns]

    required_columns = {"Label", "Task", "Session", "Start", "Durate"}
    missing = required_columns.difference(df.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise click.ClickException(f"Missing required CSV columns: {missing_text}")

    for column in ("Label", "Task", "Session", "Start", "Durate"):
        df[column] = df[column].astype(str).str.strip()

    try:
        df["Duration_Delta"] = df["Durate"].map(string_to_timedelta)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    # Parse only absolute datetimes: "after <Label>" rows are dependency references.
    absolute_start_mask = ~df["Start"].str.match(r"(?i)^after\s+")
    df["Start_Values"] = pd.NaT
    df.loc[absolute_start_mask, "Start_Values"] = pd.to_datetime(
        df.loc[absolute_start_mask, "Start"],
        errors="coerce",
        format="mixed",
    )
    df["End"] = pd.NaT
    label_to_end: dict[str, pd.Timestamp] = {}
    unresolved = list(df.index)

    while unresolved:
        progress = False
        for index in unresolved.copy():
            row = df.loc[index]
            start_value = row["Start_Values"]
            if pd.isna(start_value):
                dependency = _parse_after_reference(row["Start"])
                if dependency is None:
                    raise click.ClickException(
                        f"Invalid start value for row {index + 1}: {row['Start']!r}. "
                        "Use an absolute date/time or 'after <Label>'."
                    )
                start_value = label_to_end.get(dependency)
                if start_value is None:
                    continue

            end_value = start_value + row["Duration_Delta"]
            df.at[index, "Start_Values"] = start_value
            df.at[index, "End"] = end_value
            label_to_end[row["Label"]] = end_value
            unresolved.remove(index)
            progress = True

        if not progress:
            unresolved_rows = ", ".join(str(i + 1) for i in unresolved)
            raise click.ClickException(
                "Cannot resolve one or more 'after <Label>' dependencies. "
                f"Unresolved rows: {unresolved_rows}."
            )

    df["End"] = pd.to_datetime(df["End"])
    project_start = df["Start_Values"].min()
    df["Start_Num"] = (df["Start_Values"] - project_start).dt.days
    df["End_Num"] = (df["End"] - project_start).dt.days
    df["Day_Start_2_End"] = df["End_Num"] - df["Start_Num"]

    sessions = pd.unique(df["Session"])
    cdict = buildCD(sessions)
    df["color"] = df["Session"].map(cdict)

    if show:
        console = Console()
        console.print("Input Data:")
        console.print(original_df)
        console.print("Output Data:")
        console.print(df)
        ctx.exit()

    return df


def visualize(
    df: pd.DataFrame,
    title: str = "Gantt PLOT",
    step: int = 1,
    outputFile: Path | None = None,
    display: bool = False,
    no_sessions: bool = False,
) -> None:
    if df.empty:
        raise click.ClickException("The input CSV has no rows to plot.")

    step = max(1, step)
    dpi = 100 if display else 300
    project_start = df["Start_Values"].min()

    fig, (ax, ax1) = plt.subplots(
        2,
        figsize=(20, 6),
        gridspec_kw={"height_ratios": [6, 1]},
        facecolor="#36454F",
        dpi=dpi,
    )

    ax.set_facecolor("#36454F")
    ax1.set_facecolor("#36454F")
    ax.barh(
        df["Task"],
        df["Day_Start_2_End"],
        left=df["Start_Num"],
        color=df["color"],
        alpha=0.5,
        height=0.6,
    )

    for row in df.itertuples():
        ax.text(
            row.Start_Num + (row.Day_Start_2_End / 2), #type: ignore
            row.Task,
            row.Task,
            va="center",
            ha="center",
            alpha=0.8,
            color="w",
        )

    sessions = pd.unique(df["Session"])
    c_dict = buildCD(sessions)
    if not no_sessions:
        session_offset = -0.6
        draw_background = False
        for _, session_df in df.groupby("Session", sort=False):
            if draw_background:
                ax.axhspan(
                    session_offset,
                    session_offset + len(session_df),
                    facecolor="#FFFFFF",
                    alpha=0.2,
                )
            draw_background = not draw_background
            session_offset += len(session_df)

    ax.set_axisbelow(True)
    ax.xaxis.grid(color="k", linestyle="dashed", alpha=0.4, which="both")

    month_starts = pd.date_range(
        project_start.normalize(), end=df["End"].max(), freq="MS"
    )
    tick_positions = (month_starts - project_start).days
    visible_ticks = tick_positions >= 0
    tick_positions = tick_positions[visible_ticks]
    tick_labels = month_starts[visible_ticks].strftime("%m/%y")
    ax.set_xticks(tick_positions[::step])
    ax.set_xticklabels(tick_labels[::step], color="w")
    ax.set_yticks([])

    plt.setp([ax.get_xticklines()], color="w")
    ax.set_xlim(0, df["End_Num"].max())

    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["left"].set_position(("outward", 10))
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_color("w")
    plt.suptitle(title, color="w")

    legend_elements = [Patch(facecolor=c_dict[session], label=session) for session in sessions]
    legend = ax1.legend(
        handles=legend_elements,
        loc="upper center",
        ncol=max(1, min(5, len(legend_elements))),
        frameon=False,
    )
    plt.setp(legend.get_texts(), color="w")

    ax1.spines["right"].set_visible(False)
    ax1.spines["left"].set_visible(False)
    ax1.spines["top"].set_visible(False)
    ax1.spines["bottom"].set_visible(False)
    ax1.set_xticks([])
    ax1.set_yticks([])

    if display:
        plt.show()
    else:
        plt.savefig(outputFile, facecolor="#36454F", bbox_inches="tight")
    plt.close(fig)


def show_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    Console().print(
        f"[bold]gantty[/] Version [cyan bold]{__version__}[/] \nCopyright (C) 2025  Romolo Politi"
    )
    ctx.exit()


@click.command()
@click.option(
    "-i",
    "--input",
    metavar="FILE",
    type=click.Path(
        path_type=Path,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    help="The CSV input file. The default is gantt.csv",
    default=Path("./gantt.csv").expanduser(),
)
@click.option(
    "-o",
    "--output",
    metavar="FILE",
    type=click.Path(path_type=Path, file_okay=True, dir_okay=False, writable=True),
    help="The PNG output file. The default is gantt.png",
    default=Path("./gantt.png").expanduser(),
)
@click.option("-t", "--title", metavar="TITLE", help="Title of the plot", default="Gantt Plot")
@click.option(
    "-x",
    "--xticks",
    metavar="NUM",
    type=int,
    help="Set the x ticks frequency to NUM. The default is every month (1)",
    default=1,
)
@click.option(
    "-s",
    "--show",
    is_flag=True,
    help="Print the input data and the computed one and exit",
    default=False,
)
@click.option(
    "-d",
    "--display",
    is_flag=True,
    help="Display the plot. No output will be saved",
    default=False,
)
@click.option(
    "-n", "--no-sessions", is_flag=True, help="Do not use session colors", default=False
)
@click.option(
    "--version",
    is_flag=True,
    help="Print the version and exit",
    callback=show_version,
    expose_value=False,
    is_eager=True,
)
@click.pass_context
def main(
    ctx, input: Path, output: Path, title: str, xticks: int, show: bool, display: bool, no_sessions: bool
):
    df = build(ctx, input, show)
    visualize(df, title, outputFile=output, display=display, step=xticks, no_sessions=no_sessions)


if __name__ == "__main__":
    main()
