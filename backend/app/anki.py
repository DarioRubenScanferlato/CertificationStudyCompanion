"""Anki export functionality for exercises."""

import genanki

from app.models import MCQ


def export_to_anki(exercises: list[MCQ], output_path: str) -> None:
    """
    Export MCQ exercises to Anki .apkg format.

    Args:
        exercises: List of MCQ exercises to export
        output_path: Path where to save the .apkg file

    Raises:
        ValueError: If exercises list is empty
        IOError: If file cannot be written
    """
    if not exercises:
        raise ValueError("Cannot export empty exercise list")

    # Create a unique deck ID based on a constant (for reproducibility)
    deck_id = 2023112301
    deck_name = "Databricks DE Certification"

    # Create the deck
    deck = genanki.Deck(deck_id, deck_name)

    # Create a model for the notes
    # This defines the card structure: Front, Back, Extra, Tags
    model = genanki.Model(
        1234567890,  # model id (unique per model)
        "Databricks DE MCQ",
        fields=[
            {"name": "Question"},
            {"name": "Options"},
            {"name": "Explanation"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Question}}<br>{{Options}}",  # Question side
                "afmt": '{{FrontSide}}<hr id="answer">{{Explanation}}',  # Answer side
            }
        ],
    )

    # Add exercises as notes
    for exercise in exercises:
        # Format options as readable text
        options_text = "<br>".join(
            [
                f"{'✓ ' if opt.id in exercise.answer else '✗ '}{opt.id.upper()}. {opt.text}"
                for opt in exercise.options
            ]
        )

        # Create tags from domain, difficulty, source, and custom tags
        tags = [
            exercise.domain.value.lower().replace(" ", "_"),
            exercise.difficulty.value,
            f"source:{exercise.source.lower().replace(' ', '_')}",
        ]
        tags.extend(exercise.tags)

        # Create the note
        note = genanki.Note(
            model=model,
            fields=[
                exercise.question,
                options_text,
                exercise.explanation,
            ],
            tags=tags,
            guid=exercise.id,  # Use exercise ID as unique identifier
        )

        deck.add_note(note)

    # Create the package and write to file
    package = genanki.Package(deck)
    package.write_to_file(output_path)


def get_deck_info(output_path: str) -> dict:
    """
    Get information about an exported deck.

    Args:
        output_path: Path to the .apkg file

    Returns:
        Dictionary with deck information (name, card count)
    """
    import zipfile

    try:
        with zipfile.ZipFile(output_path, "r") as zip_ref:
            # Read collection.anki2 metadata
            # The deck name and card count are in the collection database
            # For simplicity, we'll just verify the file structure
            files = zip_ref.namelist()

            has_collection = "collection.anki2" in files
            has_media = "media" in files

            return {
                "valid": has_collection and has_media,
                "has_collection": has_collection,
                "has_media": has_media,
            }
    except Exception as e:
        return {"valid": False, "error": str(e)}
