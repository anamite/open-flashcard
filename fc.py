import csv
import json
import sys
import random

import markdown
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLineEdit, QLabel, QListWidget, QStackedWidget,
                               QDialog, QDialogButtonBox, QFileDialog, QMessageBox, QTextEdit, QFormLayout, QGroupBox,
                               QInputDialog)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QColor, QIcon, QFont
import sqlite3


class FlashcardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Open Flashcards")
        self.setMinimumWidth(600)
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0d101d;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #343444;
                color: #bfb6b0;
                border: none;
                font-size: 13px;
                font-weight: bold;
                padding: 5px;
                height: 50px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #484857;
            }
            QLineEdit {
                background-color: #3D3D3D;
                color: #FFFFFF;
                border: 1px solid #5A5A5A;
                padding: 3px;
            }
            QListWidget {
                background-color: #333742;
                color: #e5e6e9;
                border: 1px solid #5A5A5A;
            }
            QGroupBox {
                border: 1px solid #454951;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                color: #bfb6b0;
                padding: 5px;
            }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        self.setup_main_page()
        self.setup_add_card_page()
        self.setup_review_page()
        self.setup_wrong_answers_page()

        self.db_connection = sqlite3.connect("flashcards.db")
        self.create_table()

    def setup_main_page(self):
        main_page = QWidget()
        main_layout = QVBoxLayout(main_page)

        # Create a group box for each section
        add_card_group = QGroupBox()
        review_group = QGroupBox()
        wrong_answers_group = QGroupBox()
        import_group = QGroupBox()
        main_heading = QLabel("Open Flashcards")
        main_heading.setStyleSheet("font-size: 22px; font-weight: bold; color: #bfb6b0;")
        main_heading.setAlignment(Qt.AlignCenter)

        # Create a form layout for each group box
        add_card_layout = QFormLayout(add_card_group)
        review_layout = QFormLayout(review_group)
        wrong_answers_layout = QFormLayout(wrong_answers_group)
        import_layout = QFormLayout(import_group)
        import_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        # Create buttons and add them to the form layouts
        add_button = QPushButton("Add New Cards")
        icon = QIcon('add_dict.png')
        icon.addFile('add_dict.png', QSize(45, 45))
        add_button.setIcon(icon)
        add_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        add_card_layout.addRow(add_button)

        review_button = QPushButton("Start Flashcards")
        review_button.clicked.connect(self.start_review)
        review_layout.addRow(review_button)

        review_wrong_button = QPushButton("Open redo cards")
        review_wrong_button.clicked.connect(self.start_review_wrong)
        review_layout.addRow(review_wrong_button)

        wrong_answers_button = QPushButton("View")
        wrong_answers_button.clicked.connect(self.show_wrong_answers)
        wrong_answers_layout.addRow(wrong_answers_button)

        import_button = QPushButton("Import Database")
        import_button.clicked.connect(self.import_questions)
        import_layout.addRow(import_button)

        import_dict_button = QPushButton("Import Dictionary")
        import_dict_button.clicked.connect(self.import_dictionary)
        import_layout.addRow(import_dict_button)

        export_csv_button = QPushButton("Export to CSV")
        export_csv_button.clicked.connect(self.export_to_csv)
        import_layout.addRow(export_csv_button)

        # Add the group boxes to the main layout
        main_layout.addWidget(main_heading)
        main_layout.addWidget(add_card_group)
        main_layout.addWidget(review_group)
        main_layout.addWidget(wrong_answers_group)
        main_layout.addWidget(import_group)

        self.stacked_widget.addWidget(main_page)

    def import_dictionary(self):
        # Get the dictionary string from the user
        dict_string, ok = QInputDialog.getText(self, "Import Dictionary", "Enter the dictionary string:",)


        # If the user clicked OK and the string is not empty
        if ok and dict_string:
            try:
                # Convert the string to a dictionary
                data = json.loads(dict_string)

                # Check if the data is a list of dictionaries with "question" and "answer" keys
                if isinstance(data, list) and all(
                        isinstance(item, dict) and "question" in item and "answer" in item for item in data):
                    # Insert the data into the database
                    cursor = self.db_connection.cursor()
                    cursor.executemany("INSERT INTO flashcards (question, answer) VALUES (:question, :answer)", data)
                    self.db_connection.commit()

                    QMessageBox.information(self, "Import Successful", f"Imported {len(data)} questions.")
                else:
                    QMessageBox.warning(self, "Import Failed",
                                        "Invalid dictionary format. The data should be a list of dictionaries with 'question' and 'answer' keys.")
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Import Failed",
                                    "Invalid dictionary string. Please enter a valid JSON string.")

    def setup_add_card_page(self):
        add_card_page = QWidget()
        add_card_layout = QVBoxLayout(add_card_page)

        self.question_input = QTextEdit()
        self.question_input.setPlaceholderText("Enter question")
        add_card_layout.addWidget(self.question_input)

        self.answer_input = QTextEdit()
        self.answer_input.setPlaceholderText("Enter answer")
        add_card_layout.addWidget(self.answer_input)

        save_button = QPushButton("Save Card")
        save_button.clicked.connect(self.save_card)
        add_card_layout.addWidget(save_button)

        back_button = QPushButton("Back to Main")
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        add_card_layout.addWidget(back_button)

        self.stacked_widget.addWidget(add_card_page)

    def setup_review_page(self):
        self.review_page = QWidget()
        review_layout = QVBoxLayout(self.review_page)

        self.card_label = QLabel("Question will appear here")
        self.card_label.setWordWrap(True)
        self.card_label.setAlignment(Qt.AlignCenter)
        self.card_label.setStyleSheet("""
            background-color: #171b26; 
            border-radius: 15px; 
            padding: 50px;
            color: #e5e6e9;
            font-size: 22px;
            font-weight: medium;
        """)
        review_layout.addWidget(self.card_label)

        button_layout = QHBoxLayout()

        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_card)
        button_layout.addWidget(edit_button)

        self.view_answer_button = QPushButton("View Answer")
        self.view_answer_button.clicked.connect(self.view_answer)
        button_layout.addWidget(self.view_answer_button)

        correct_button = QPushButton("Correct")
        correct_button.setStyleSheet(
            "background-color: #343444; color: #70a266; font-weight: bold; padding: 5px; border-radius: 3px;"
        )
        correct_button.clicked.connect(self.mark_correct)
        button_layout.addWidget(correct_button)

        wrong_button = QPushButton("Redo")
        wrong_button.setStyleSheet(
            "background-color: #343444; color: #cf6632; font-weight: bold;"
            "font-size: 14px; padding: 5px; border-radius: 3px;"
        )
        wrong_button.clicked.connect(self.mark_wrong)
        button_layout.addWidget(wrong_button)

        review_layout.addLayout(button_layout)

        back_button = QPushButton("Back to Main")
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        review_layout.addWidget(back_button)

        self.stacked_widget.addWidget(self.review_page)

    def setup_wrong_answers_page(self):
        self.wrong_answers_page = QWidget()
        wrong_answers_layout = QVBoxLayout(self.wrong_answers_page)

        self.wrong_answers_list = QListWidget()
        wrong_answers_layout.addWidget(self.wrong_answers_list)

        reset_button = QPushButton("Reset Selected to Correct")
        reset_button.clicked.connect(self.reset_wrong_answers)
        wrong_answers_layout.addWidget(reset_button)

        back_button = QPushButton("Back to Main")
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        wrong_answers_layout.addWidget(back_button)

        self.stacked_widget.addWidget(self.wrong_answers_page)

    def create_table(self):
        cursor = self.db_connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                correct INTEGER DEFAULT 0,
                wrong INTEGER DEFAULT 0
            )
        """)
        self.db_connection.commit()

    def save_card(self):
        question = self.question_input.toPlainText()
        # get answer from the text input
        answer = self.answer_input.toPlainText()

        if question and answer:
            cursor = self.db_connection.cursor()
            cursor.execute("INSERT INTO flashcards (question, answer) VALUES (?, ?)", (question, answer))
            self.db_connection.commit()
            self.question_input.clear()
            self.answer_input.clear()
            self.animate_save()

    def animate_save(self):
        self.animation = QPropertyAnimation(self.question_input, b"geometry")
        self.animation.setDuration(220)
        self.animation.setStartValue(self.question_input.geometry())
        self.animation.setEndValue(self.question_input.geometry().translated(50, 0))
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.animation2 = QPropertyAnimation(self.question_input, b"geometry")
        self.animation2.setDuration(250)
        self.animation2.setStartValue(self.question_input.geometry().translated(50, 0))
        self.animation2.setEndValue(self.question_input.geometry())
        self.animation2.setEasingCurve(QEasingCurve.InOutQuad)

        self.animation.finished.connect(self.animation2.start)
        self.animation.start()

    def animate_card(self, direction):
        if direction == "up":
            translation = (0, -20)
        elif direction == "down":
            translation = (0, 10)
        elif direction == "left":
            translation = (-55, 0)
        elif direction == "right":
            translation = (55, 0)
        else:
            print(f"Unknown direction: {direction}")
            return

        self.animation = QPropertyAnimation(self.card_label, b"geometry")
        self.animation.setDuration(120)
        self.animation.setStartValue(self.card_label.geometry())
        self.animation.setEndValue(self.card_label.geometry().translated(*translation))
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.animation2 = QPropertyAnimation(self.card_label, b"geometry")
        self.animation2.setDuration(120)
        self.animation2.setStartValue(self.card_label.geometry().translated(*translation))
        self.animation2.setEndValue(self.card_label.geometry())
        self.animation2.setEasingCurve(QEasingCurve.InOutQuad)

        self.animation.finished.connect(self.animation2.start)
        self.animation.start()

    def view_answer(self):
        if self.current_card_index < len(self.current_cards):
            card = self.current_cards[self.current_card_index]
            answer_html = markdown.markdown(card[2])  # Convert Markdown to HTML
            # left text align , the content / div should be in the center but just the text should be left aligne

            self.card_label.setText(answer_html)  # Set the HTML text
            self.card_label.setStyleSheet(
                "background-color: #171b26;"
                "border: 1px solid #6e7593;"
                "border-radius: 15px; padding: 40px; color: #e5e6e9; font-size: 22px;"
                "text-align: left;"
                "font-weight: medium;"
            )
            self.view_answer_button.setText("Back")
            self.view_answer_button.setStyleSheet(
                "background-color: #6e7593; color: #171b26; font-weight: bold; padding: 5px; border-radius: 3px;"
            )
            self.view_answer_button.clicked.disconnect()
            self.view_answer_button.clicked.connect(self.view_question)
            self.animate_card("up")

    def view_question(self):
        if self.current_card_index < len(self.current_cards):
            card = self.current_cards[self.current_card_index]
            self.card_label.setText(card[1])  # Show question
            self.card_label.setStyleSheet("""
                background-color: #171b26; 
                border-radius: 15px; 
                padding: 50px;
                color: #e5e6e9;
                font-size: 22px;
                font-weight: medium;
            """)
            self.view_answer_button.setText("View Answer")
            self.view_answer_button.setStyleSheet(
                "background-color: #343444; color: #bfb6b0; font-weight: bold; padding: 5px; border-radius: 3px;"
            )
            self.view_answer_button.clicked.disconnect()
            self.view_answer_button.clicked.connect(self.view_answer)
            self.animate_card("down")

    def export_to_csv(self):
        # Retrieve all the questions and answers from the database
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT question, answer FROM flashcards")
        flashcards = cursor.fetchall()

        # Write them to a CSV file
        with open('cards.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # writer.writerow(["Question", "Answer"])  # Write the header
            writer.writerows(flashcards)  # Write the data

        QMessageBox.information(self, "Export Successful", "The CSV file has been successfully exported.")

    def start_review(self):
        self.current_cards = self.get_all_cards()
        if self.current_cards:
            random.shuffle(self.current_cards)
            self.current_card_index = 0
            self.show_next_card()
            self.stacked_widget.setCurrentIndex(2)
        else:
            self.card_label.setText("No cards available. Add some cards first!")

    def get_wrong_cards(self):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id, question, answer FROM flashcards WHERE wrong > 0")
        return cursor.fetchall()

    def start_review_wrong(self):
        self.current_cards = self.get_wrong_cards()
        if self.current_cards:
            random.shuffle(self.current_cards)
            self.current_card_index = 0
            self.show_next_card()
            self.stacked_widget.setCurrentIndex(2)
        else:
            self.card_label.setText("No wrong cards available. Mark some cards as wrong first!")

    def get_all_cards(self):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id, question, answer FROM flashcards")
        return cursor.fetchall()

    # Modify your show_next_card method like this:
    def show_next_card(self):

        self.view_answer_button.setStyleSheet(
            "background-color: #343444; color: #bfb6b0; font-weight: bold; padding: 5px; border-radius: 3px;"
        )
        self.view_answer_button.setText("View Answer")
        self.card_label.setStyleSheet("""
            background-color: #171b26; 
            border-radius: 15px; 
            padding: 50px;
            color: #e5e6e9;
            font-size: 22px;
            font-weight: medium;
        """)

        if self.current_card_index < len(self.current_cards):
            card = self.current_cards[self.current_card_index]
            self.card_label.setText(card[1])  # Show question
            self.current_card_id = card[0]
        else:
            # Get the number of correct answers
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM flashcards WHERE correct = 1")
            correct_answers = cursor.fetchone()[0]
            # Update the review progress label
            self.card_label.setFont(QFont('Arial', 22))  # Set the font to Arial with size 20
            self.card_label.setText(f"Review completed!\n \nYou answered {correct_answers} questions correctly!")

    def mark_correct(self):
        self.update_card_status(self.current_card_id, correct=True)
        self.animate_card("right")
        self.next_card()

    def mark_wrong(self):
        self.update_card_status(self.current_card_id, correct=False)
        self.animate_card("left")
        self.next_card()

    def update_card_status(self, card_id, correct):
        cursor = self.db_connection.cursor()
        if correct:
            cursor.execute("UPDATE flashcards SET correct = 1 WHERE id = ?", (card_id,))
            cursor.execute("UPDATE flashcards SET wrong = 0 WHERE id = ?", (card_id,))
        else:
            cursor.execute("UPDATE flashcards SET wrong = 1 WHERE id = ?", (card_id,))
            cursor.execute("UPDATE flashcards SET correct = 0 WHERE id = ?", (card_id,))
        self.db_connection.commit()

    def next_card(self):
        self.current_card_index += 1
        self.show_next_card()

    def edit_card(self):
        if self.current_card_index < len(self.current_cards):
            card = self.current_cards[self.current_card_index]
            dialog = EditCardDialog(card[1], card[2])
            if dialog.exec():
                new_question, new_answer = dialog.get_data()
                cursor = self.db_connection.cursor()
                cursor.execute("UPDATE flashcards SET question = ?, answer = ? WHERE id = ?",
                               (new_question, new_answer, card[0]))
                self.db_connection.commit()
                self.current_cards[self.current_card_index] = (card[0], new_question, new_answer)
                self.show_next_card()

    def show_wrong_answers(self):
        self.wrong_answers_list.clear()
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id, question FROM flashcards WHERE wrong > 0")
        wrong_cards = cursor.fetchall()
        for card in wrong_cards:
            self.wrong_answers_list.addItem(f"{card[0]}: {card[1]}")
        self.stacked_widget.setCurrentIndex(3)

    def reset_wrong_answers(self):
        selected_items = self.wrong_answers_list.selectedItems()
        if not selected_items:
            return

        cursor = self.db_connection.cursor()
        for item in selected_items:
            card_id = int(item.text().split(':')[0])
            cursor.execute("UPDATE flashcards SET wrong = 0 WHERE id = ?", (card_id,))
        self.db_connection.commit()
        self.show_wrong_answers()  # Refresh the list

    def import_questions(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Database File", "", "SQLite Database (*.db)")
        if file_name:
            try:
                import_connection = sqlite3.connect(file_name)
                import_cursor = import_connection.cursor()
                import_cursor.execute("SELECT question, answer FROM flashcards")
                imported_cards = import_cursor.fetchall()
                import_connection.close()

                cursor = self.db_connection.cursor()
                for question, answer in imported_cards:
                    cursor.execute("SELECT COUNT(*) FROM flashcards WHERE question = ?", (question,))
                    if cursor.fetchone()[0] == 0:
                        cursor.execute("INSERT INTO flashcards (question, answer) VALUES (?, ?)", (question, answer))
                self.db_connection.commit()

                QMessageBox.information(self, "Import Successful", f"Imported {len(imported_cards)} unique questions.")
            except sqlite3.Error as e:
                QMessageBox.warning(self, "Import Failed", f"Error importing questions: {str(e)}")


class EditCardDialog(QDialog):
    def __init__(self, question, answer):
        super().__init__()

        self.setWindowTitle("Edit Card")
        layout = QVBoxLayout(self)

        self.question_edit = QTextEdit(question)
        self.answer_edit = QTextEdit(answer)
        layout.addWidget(QLabel("Question:"))
        layout.addWidget(self.question_edit)
        layout.addWidget(QLabel("Answer:"))
        layout.addWidget(self.answer_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return self.question_edit.toPlainText(), self.answer_edit.toPlainText()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlashcardApp()
    window.resize(300, 400)
    window.show()
    sys.exit(app.exec())
