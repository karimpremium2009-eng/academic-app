import flet as ft
import datetime
import os
import asyncio  # ADDED: For asynchronous execution
from core import SubjectData, get_classification
from pdf_service import PDFReportGenerator

# --- 🎨 THEME CONSTANTS ---
COLOR_BG = "#0f0f12"
COLOR_SURFACE = "#1e1e24"
COLOR_PRIMARY = "#6c5ce7"
COLOR_ACCENT = "#a29bfe"
COLOR_SUCCESS = "#00b894"
COLOR_ERROR = "#d63031"


def get_transparent_color(color_hex, opacity):
    """
    Helper to apply opacity to hex colors for latest Flet versions.
    Converts #RRGGBB to #AARRGGBB.
    """
    if color_hex.startswith("#"):
        hex_val = color_hex.lstrip("#")
        if len(hex_val) == 6:
            alpha = int(opacity * 255)
            return f"#{alpha:02x}{hex_val}"
    return color_hex


def main(page: ft.Page):
    print("Page is loading...")  # DEBUG PRINT

    # --- 📱 PAGE CONFIGURATION ---
    page.title = "Academic Pro"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = COLOR_BG
    page.padding = 0

    # Window properties namespace
    page.window.width = 400
    page.window.height = 850
    page.window.resizable = True

    # --- STATE ---
    ui_cards = []

    # --- COMPONENT: SUBJECT CARD WRAPPER ---
    class SubjectCardWrapper:
        def __init__(self, index):
            self.index = index
            self.txt_name = ft.TextField(
                label=f"Subject {index}",
                border_color=COLOR_PRIMARY,
                text_size=16,
                border_radius=10,
                cursor_color=COLOR_ACCENT
            )
            # FIXED: ft.Colors (Capital C)
            self.txt_coeff_display = ft.Text("Coeff: 1", color=ft.Colors.GREY)
            self.slider_coeff = ft.Slider(
                min=1, max=10, divisions=9, value=1,
                active_color=COLOR_PRIMARY,
                on_change=lambda e: self.update_coeff_label(e.control.value)
            )
            self.grades_column = ft.Column(spacing=10)

            # ControlState is correct for Flet 0.26.0+
            self.exams_segment = ft.SegmentedButton(
                selected={"1"},
                allow_multiple_selection=False,
                on_change=self.on_exam_count_change,
                segments=[
                    ft.Segment(value="1", label=ft.Text("1")),
                    ft.Segment(value="2", label=ft.Text("2")),
                    ft.Segment(value="3", label=ft.Text("3")),
                    ft.Segment(value="4", label=ft.Text("4"))
                ],
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.SELECTED: COLOR_PRIMARY, "": COLOR_SURFACE},
                    # FIXED: ft.Colors (Capital C)
                    color=ft.Colors.WHITE
                )
            )
            self.grade_inputs = []
            self.add_grade_input(1)

            self.ui = ft.Container(
                bgcolor=COLOR_SURFACE, border_radius=15, padding=20,
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"#{index}", size=18, weight="bold", color=COLOR_PRIMARY),
                        ft.VerticalDivider(width=10),
                        ft.Container(content=self.txt_name, expand=True)
                    ]),
                    # FIXED: ft.Colors (Capital C)
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Row([ft.Text("Coefficient", size=12), self.txt_coeff_display],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    self.slider_coeff,
                    ft.Text("Number of Exams", size=12),
                    self.exams_segment,
                    # FIXED: ft.Colors (Capital C)
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    self.grades_column
                ])
            )

        def update_coeff_label(self, value):
            self.txt_coeff_display.value = f"Coeff: {int(value)}"
            page.update()

        def add_grade_input(self, exam_num):
            border_col = get_transparent_color(COLOR_PRIMARY, 0.5)

            inp = ft.TextField(
                label=f"Exam {exam_num} (/20)",
                border_color=border_col,
                keyboard_type=ft.KeyboardType.NUMBER,
                height=50,
                border_radius=10,
                text_size=14,
                cursor_color=COLOR_ACCENT
            )
            self.grades_column.controls.append(inp)
            self.grade_inputs.append(inp)

        def on_exam_count_change(self, e):
            if not e.control.selected: return
            count = int(list(e.control.selected)[0])
            self.grades_column.controls.clear()
            self.grade_inputs.clear()
            for i in range(1, count + 1): self.add_grade_input(i)
            page.update()

        def extract_data(self):
            name = self.txt_name.value.strip()
            if not name: raise ValueError(f"Subject #{self.index} name is missing.")
            raw_grades = []
            for inp in self.grade_inputs:
                try:
                    if not inp.value: raise ValueError
                    val = float(inp.value)
                    if not (0 <= val <= 20): raise ValueError
                    raw_grades.append(val)
                except ValueError:
                    raise ValueError(f"Invalid grade in '{name}' (Must be 0-20)")
            return SubjectData(self.index, name, int(self.slider_coeff.value), raw_grades)

    # --- APP ACTIONS ---
    def go_input(e):
        try:
            count = int(slider_setup_count.value)
            lv_inputs.controls.clear()
            ui_cards.clear()
            for i in range(1, count + 1):
                card = SubjectCardWrapper(i)
                ui_cards.append(card)
                lv_inputs.controls.append(card.ui)
            page.go("/input")
        except Exception as ex:
            print(f"Error: {ex}")

    def calculate_results(e):
        try:
            processed_subjects = []
            for wrapper in ui_cards:
                data = wrapper.extract_data()
                data.calculate()
                processed_subjects.append(data)

            total_w = sum(s.weighted_score for s in processed_subjects)
            total_c = sum(s.coeff for s in processed_subjects)
            final_avg = total_w / total_c if total_c > 0 else 0
            text, color_hex = get_classification(final_avg)

            lbl_final_score.value = f"{final_avg:.2f}"
            lbl_class_text.value = text.upper()
            cont_class_badge.bgcolor = color_hex

            lv_results_breakdown.controls.clear()
            for s in processed_subjects:
                lv_results_breakdown.controls.append(
                    ft.Container(
                        bgcolor=COLOR_SURFACE, padding=15, border_radius=10,
                        content=ft.Row([
                            # FIXED: ft.Colors (Capital C)
                            ft.Text(s.name, weight="bold", size=16, color=ft.Colors.WHITE, expand=True),
                            ft.Column([
                                ft.Text(f"{s.average:.2f}", color=COLOR_ACCENT, weight="bold", size=16,
                                        text_align="right"),
                                # FIXED: ft.Colors (Capital C)
                                ft.Text(f"x{s.coeff}", color=ft.Colors.GREY, size=12, text_align="right")
                            ], alignment=ft.MainAxisAlignment.END)
                        ])
                    )
                )

            page.session.set("subjects", processed_subjects)
            page.session.set("avg", final_avg)
            page.session.set("class", text)

            # FIXED: show_snack_bar -> open
            page.open(ft.SnackBar(content=ft.Text("Results Calculated!"), bgcolor=COLOR_SUCCESS))
            page.go("/results")
        except ValueError as err:
            # FIXED: show_snack_bar -> open
            page.open(ft.SnackBar(ft.Text(str(err)), bgcolor=COLOR_ERROR))

    # --- MODIFIED: ASYNC EXPORT FUNCTION ---
    async def export_pdf(e):
        try:
            # 1. Show "Generating" message immediately
            page.open(ft.SnackBar(ft.Text("Generating PDF... Please wait."), bgcolor=COLOR_PRIMARY))
            page.update()

            # 2. Prepare data
            filename = f"Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            subjects = page.session.get("subjects")
            avg = page.session.get("avg")
            classification = page.session.get("class")

            gen = PDFReportGenerator()

            # 3. Run generation in a background thread to prevent freezing
            # asyncio.to_thread runs the synchronous gen.generate function in a separate thread
            success, msg = await asyncio.to_thread(gen.generate, subjects, avg, classification, filename)

            # 4. Show Result Message
            if success:
                page.open(ft.SnackBar(ft.Text(f"{msg}"), bgcolor=COLOR_SUCCESS))
            else:
                page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor=COLOR_ERROR))

        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(str(ex)), bgcolor=COLOR_ERROR))

    # --- VIEWS ---
    slider_setup_count = ft.Slider(min=1, max=10, divisions=9, value=5, label="{value}", active_color=COLOR_PRIMARY)

    view_welcome = ft.View("/", [
        ft.Container(
            padding=30, alignment=ft.alignment.center, expand=True,
            content=ft.Column([
                ft.Icon(ft.Icons.SCHOOL, size=80, color=COLOR_PRIMARY),
                ft.Text("Academic Pro", size=32, weight="bold"),
                # FIXED: ft.Colors (Capital C)
                ft.Text("Mobile Edition", color=ft.Colors.GREY),
                ft.Divider(height=40, color=ft.Colors.TRANSPARENT),
                ft.Text("How many subjects?", size=16),
                slider_setup_count,
                # FIXED: ft.Colors (Capital C)
                ft.ElevatedButton("Start Session", on_click=go_input, bgcolor=COLOR_PRIMARY, color=ft.Colors.WHITE,
                                  height=50, width=200),
                ft.Divider(height=50, color=ft.Colors.TRANSPARENT),
                ft.Text("Powered by Karim Dev", size=12, color=ft.Colors.GREY)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER)
        )
    ], bgcolor=COLOR_BG, padding=0)

    lv_inputs = ft.ListView(expand=True, spacing=15, padding=20)

    view_input = ft.View("/input", [
        # FIXED: ft.Colors (Capital C)
        ft.AppBar(title=ft.Text("Subject Details"), bgcolor=COLOR_SURFACE, color=ft.Colors.WHITE),
        lv_inputs,
        ft.Container(
            padding=20, bgcolor=COLOR_SURFACE,
            # FIXED: ft.Colors (Capital C)
            content=ft.ElevatedButton("CALCULATE RESULTS", on_click=calculate_results, bgcolor=COLOR_SUCCESS,
                                      color=ft.Colors.WHITE, height=50, width=400)
        )
    ], bgcolor=COLOR_BG, padding=0)

    lbl_final_score = ft.Text("0.00", size=60, weight="bold")
    # FIXED: ft.Colors (Capital C)
    lbl_class_text = ft.Text("STATUS", color=ft.Colors.BLACK, weight="bold")
    cont_class_badge = ft.Container(padding=10, border_radius=20, content=lbl_class_text)
    lv_results_breakdown = ft.ListView(expand=True, spacing=10, padding=20)

    view_results = ft.View("/results", [
        # FIXED: ft.Colors (Capital C)
        ft.AppBar(title=ft.Text("Performance Report"), bgcolor=COLOR_SURFACE,
                  leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/")),
                  color=ft.Colors.WHITE),
        ft.Container(
            padding=20, alignment=ft.alignment.center,
            content=ft.Column([
                ft.Container(
                    bgcolor=get_transparent_color(COLOR_PRIMARY, 0.1),
                    border=ft.border.all(1, COLOR_PRIMARY),
                    border_radius=30,
                    padding=30,
                    alignment=ft.alignment.center,
                    content=ft.Column([
                        ft.Text("FINAL AVERAGE", color=COLOR_ACCENT, size=12),
                        lbl_final_score,
                        # FIXED: ft.Colors (Capital C)
                        ft.Text("/ 20", color=ft.Colors.GREY),
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        cont_class_badge
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ),
                # FIXED: ft.Colors (Capital C)
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.Text("Subject Breakdown", size=18, weight="bold")
            ])
        ),
        lv_results_breakdown,
        ft.Container(
            padding=20, bgcolor=COLOR_SURFACE,
            # FIXED: ft.Colors (Capital C)
            content=ft.ElevatedButton("EXPORT PDF", icon=ft.Icons.PICTURE_AS_PDF, on_click=export_pdf,
                                      bgcolor=COLOR_PRIMARY, color=ft.Colors.WHITE, height=50, width=400)
        )
    ], bgcolor=COLOR_BG, padding=0)

    def route_change(route):
        page.views.clear()
        page.views.append(view_welcome)
        if page.route == "/input": page.views.append(view_input)
        if page.route == "/results": page.views.append(view_results)
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/")
    print("App Loaded!")


if __name__ == "__main__":
    ft.app(main)