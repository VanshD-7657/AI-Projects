from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet

from datetime import datetime


def generate_travel_pdf(
    pdf_path,
    user_query,
    thread_id,
    collected
):

    doc = SimpleDocTemplate(pdf_path)

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "AI Travel Planner Report",
            styles["Title"]
        )
    )

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            f"<b>User Query:</b> {user_query}",
            styles["BodyText"]
        )
    )

    story.append(
        Paragraph(
            f"<b>User ID:</b> {thread_id}",
            styles["BodyText"]
        )
    )

    story.append(
        Paragraph(
            f"<b>Generated:</b> {datetime.now()}",
            styles["BodyText"]
        )
    )

    story.append(Spacer(1, 20))

    sections = [
        ("Flight Information", collected["flight_results"]),
        ("Hotel Information", collected["hotel_results"]),
        ("Research Results", collected["research_results"]),
        ("Final Travel Plan", collected["final_response"])
    ]

    for title, text in sections:

        story.append(
            Paragraph(
                title,
                styles["Heading2"]
            )
        )

        story.append(
            Paragraph(
                str(text).replace("\n", "<br/>"),
                styles["BodyText"]
            )
        )

        story.append(Spacer(1, 15))


    doc.build(story)

    return pdf_path