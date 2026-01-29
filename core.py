# core.py
# ---------------------------------------------------------
# PURE BUSINESS LOGIC LAYER
# No UI libraries (Tkinter/Flet) allowed here.
# ---------------------------------------------------------

# --- COLOR CONSTANTS (Hex codes for UI consistency) ---
COLOR_DANGER = "#d63031"
COLOR_WARNING = "#fdcb6e"
COLOR_GOOD = "#6c5ce7"
COLOR_VERY_GOOD = "#a29bfe"
COLOR_LEGENDARY = "#a29bfe"
COLOR_ELITE = "#ffeaa7"


class SubjectData:
    """
    Data model representing a single subject.
    Holds the name, coefficient, and list of exam grades.
    """

    def __init__(self, index, name="", coeff=1, grades=None):
        self.index = index
        self.name = name
        self.coeff = coeff
        self.grades = grades if grades else []
        self.average = 0.0
        self.weighted_score = 0.0

    def calculate(self):
        """Calculates average and weighted score for this subject."""
        if not self.grades:
            self.average = 0.0
        else:
            self.average = sum(self.grades) / len(self.grades)
        self.weighted_score = self.average * self.coeff


def get_classification(average):
    """
    Determines the student's performance tier based on the average.
    Returns: (Classification Text, Hex Color)
    """
    if average < 10:
        return "Insufficient", COLOR_DANGER
    if 10 <= average < 11:
        return "Out of Danger Zone", COLOR_WARNING
    if 11 <= average < 14:
        return "Good", COLOR_GOOD
    if 14 <= average < 16:
        return "Very Good", COLOR_VERY_GOOD
    if 16 <= average < 18:
        return "Legendary", COLOR_LEGENDARY

    return "Elite Mind", COLOR_ELITE