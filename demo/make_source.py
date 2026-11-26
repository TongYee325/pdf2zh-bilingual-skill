"""Generate the original one-page example used in the README."""
from pathlib import Path

import pymupdf


def main():
    directory = Path(__file__).resolve().parent
    navy = (0.07, 0.16, 0.26)
    teal = (0.00, 0.40, 0.38)
    gray = (0.30, 0.37, 0.44)
    document = pymupdf.open()
    page = document.new_page(width=540, height=630)

    def text(y, value, size=12, bold=False, color=navy, height=70):
        bottom = page.insert_textbox(
            (48, y, 492, y + height), value,
            fontname="hebo" if bold else "helv", fontsize=size,
            lineheight=1.38, color=color,
        )
        if bottom < 0:
            raise ValueError(f"Demo text does not fit at y={y}")

    text(50, "TECHNICAL NOTE", 10, True, teal)
    text(85, "A Robot's Reaction Time", 24, True)
    text(132, "An example of asynchronous action execution", 13, color=gray)
    page.draw_line((48, 173), (492, 173), color=teal, width=1.3)
    text(202, "Observations and actions", 14, True)
    text(231, "A robot captures a camera image and uses a policy to predict a sequence of actions. The controller can execute the first action while the policy prepares its next prediction.", height=85)
    text(333, "Reaction time", 14, True)
    text(362, "Imagine that the controller runs once every 20 milliseconds and the policy needs 120 milliseconds for one prediction. A buffer prevents the controller from running out of actions. A new obstacle still needs to be detected before the next prediction can account for it.", height=105)
    text(477, "What to measure", 14, True)
    text(506, "Record the time between the arrival of a new observation and the first action that responds to it. Report that delay alongside the control frequency.", height=77)
    document.set_metadata({"title": "A Robot's Reaction Time", "subject": "Original example for the PDF2zh bilingual skill"})
    document.save(directory / "robot-reaction-time.pdf", garbage=4, deflate=True)
    document.close()


if __name__ == "__main__":
    main()
