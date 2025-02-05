import sys

import numpy as np
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
                             QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QMainWindow, QPushButton, QSlider, QSpinBox,
                             QTextEdit, QVBoxLayout, QWidget)
from scipy import ndimage


class AnimatedPixelButton(QPushButton):
    def __init__(self, row, col, button_size=30):
        super().__init__()
        self.row = row
        self.col = col
        self.state = False
        self.setFixedSize(button_size, button_size)
        self.updateStyle()

    def updateStyle(self):
        intensity = 255 if not self.state else 0  # White for 0, Black for 1
        color = QColor(intensity, intensity, intensity)
        self.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray;")


class EnhancedGridWidget(QWidget):
    gridChanged = pyqtSignal()

    def __init__(self, rows=10, cols=10, editable=False, button_size=30):
        super().__init__()
        self.rows = rows
        self.cols = cols
        self.editable = editable
        self.button_size = button_size
        self.buttons = []
        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        layout.setSpacing(0)

        for i in range(self.rows):
            row_buttons = []
            for j in range(self.cols):
                btn = AnimatedPixelButton(i, j, self.button_size)
                if self.editable:
                    btn.clicked.connect(self.buttonClicked)
                layout.addWidget(btn, i, j)
                row_buttons.append(btn)
            self.buttons.append(row_buttons)

        self.setLayout(layout)

    def buttonClicked(self):
        button = self.sender()
        button.state = not button.state
        button.updateStyle()
        self.gridChanged.emit()

    def getGrid(self):
        return np.array([[int(btn.state) for btn in row] for row in self.buttons])

    def setGrid(self, grid):
        if grid is None or len(grid) != self.rows or len(grid[0]) != self.cols:
            return
        for i in range(self.rows):
            for j in range(self.cols):
                self.buttons[i][j].state = bool(grid[i][j])
                self.buttons[i][j].updateStyle()


class OperationExplanationWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMinimumHeight(100)
        self.updateExplanation("Erosion")

    def updateExplanation(self, operation):
        explanations = {
            "Erosion": """Erosion shrinks or thins objects. It removes pixels on object boundaries,useful for eliminating small protrusions or breaking apart connected components.""",
            "Dilation": """Dilation expands or thickens objects. It adds pixels to object boundaries,useful for filling small holes or connecting nearby components.""",
            "Opening": """Opening is erosion followed by dilation. It removes small objects while preserving the shape and size of larger objects.""",
            "Closing": """Closing is dilation followed by erosion. It fills small holes and gaps while preserving the shape and size of objects.""",
        }
        self.setText(explanations.get(operation, ""))


class TextPatternGenerator:
    def __init__(self):
        # Initialize font parameters
        self.font_size = (7, 5)  # Height and width for each character

    def _get_digit_pattern(self, digit):
        """Generate pattern for a digit (0-9)"""
        grid = np.zeros(self.font_size)
        h, w = self.font_size

        if digit == "0":
            # Draw a rectangle with empty center
            grid[0, 1 : w - 1] = 1  # Top
            grid[h - 1, 1 : w - 1] = 1  # Bottom
            grid[1 : h - 1, 0] = 1  # Left
            grid[1 : h - 1, w - 1] = 1  # Right
        elif digit == "1":
            grid[:, w // 2] = 1  # Vertical line
            grid[0, w // 2 - 1 : w // 2 + 1] = 1  # Top serif
            grid[h - 1, w // 2 - 1 : w // 2 + 1] = 1  # Base
        elif digit == "2":
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[h - 1, :] = 1  # Bottom
            grid[1 : h // 2, w - 1] = 1  # Top right
            grid[h // 2 + 1 : h - 1, 0] = 1  # Bottom left
        elif digit == "3":
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[h - 1, :] = 1  # Bottom
            grid[1 : h - 1, w - 1] = 1  # Right side
        elif digit == "4":
            grid[: h // 2 + 1, 0] = 1  # Left top
            grid[h // 2, :] = 1  # Middle
            grid[:, w - 1] = 1  # Right side
        elif digit == "5":
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[h - 1, :] = 1  # Bottom
            grid[1 : h // 2, 0] = 1  # Top left
            grid[h // 2 + 1 : h - 1, w - 1] = 1  # Bottom right
        elif digit == "6":
            grid[:, 0] = 1  # Left side
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[h - 1, :] = 1  # Bottom
            grid[h // 2 :, w - 1] = 1  # Bottom right
        elif digit == "7":
            grid[0, :] = 1  # Top
            grid[:, w - 1] = 1  # Right side
        elif digit == "8":
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[h - 1, :] = 1  # Bottom
            grid[:, 0] = 1  # Left side
            grid[:, w - 1] = 1  # Right side
        elif digit == "9":
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[h - 1, :] = 1  # Bottom
            grid[: h // 2, 0] = 1  # Top left
            grid[:, w - 1] = 1  # Right side

        return grid

    def _get_letter_pattern(self, letter):
        """Generate pattern for a letter (A-Z)"""
        grid = np.zeros(self.font_size)
        h, w = self.font_size

        if letter == "A":
            grid[1:, 0] = 1  # Left side
            grid[1:, w - 1] = 1  # Right side
            grid[0, 1 : w - 1] = 1  # Top
            grid[h // 2, 1 : w - 1] = 1  # Middle
        elif letter == "B":
            grid[:, 0] = 1  # Left side
            grid[0, : w - 1] = 1  # Top
            grid[h - 1, : w - 1] = 1  # Bottom
            grid[h // 2, : w - 1] = 1  # Middle
            grid[1 : h // 2, w - 1] = 1  # Top right
            grid[h // 2 + 1 : h - 1, w - 1] = 1  # Bottom right
        elif letter == "C":
            grid[1 : h - 1, 0] = 1  # Left side
            grid[0, 1:] = 1  # Top
            grid[h - 1, 1:] = 1  # Bottom
        elif letter == "D":
            grid[:, 0] = 1  # Left side
            grid[0, : w - 1] = 1  # Top
            grid[h - 1, : w - 1] = 1  # Bottom
            grid[1 : h - 1, w - 1] = 1  # Right side
        elif letter == "E":
            grid[:, 0] = 1  # Left side
            grid[0, :] = 1  # Top
            grid[h - 1, :] = 1  # Bottom
            grid[h // 2, :] = 1  # Middle
        elif letter == "F":
            grid[:, 0] = 1  # Left side
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
        elif letter == "G":
            grid[1 : h - 1, 0] = 1  # Left side
            grid[0, 1:] = 1  # Top
            grid[h - 1, 1:] = 1  # Bottom
            grid[h // 2 : h - 1, w - 1] = 1  # Bottom right
            grid[h // 2, h // 2 :] = 1  # Middle right
        elif letter == "H":
            grid[:, 0] = 1  # Left side
            grid[:, w - 1] = 1  # Right side
            grid[h // 2, :] = 1  # Middle
        elif letter == "I":
            grid[0, :] = 1  # Top
            grid[h - 1, :] = 1  # Bottom
            grid[:, w // 2] = 1  # Middle vertical
        elif letter == "J":
            grid[0, :] = 1  # Top
            grid[:, w - 1] = 1  # Right side
            grid[h - 1, : w - 1] = 1  # Bottom
            grid[h - 2, 0] = 1  # Bottom left corner
        elif letter == "K":
            grid[:, 0] = 1  # Left side
            for i in range(h):
                j = abs(i - h // 2)
                if j < w - 1:
                    grid[i, w - 1 - j] = 1
        elif letter == "L":
            grid[:, 0] = 1  # Left side
            grid[h - 1, :] = 1  # Bottom
        elif letter == "M":
            grid[:, 0] = 1  # Left side
            grid[:, w - 1] = 1  # Right side
            grid[1 : h // 2, w // 2] = 1  # Middle
            grid[0, w // 2] = 1  # Top middle
        elif letter == "N":
            grid[:, 0] = 1  # Left side
            grid[:, w - 1] = 1  # Right side
            for i in range(h):
                grid[i, i * (w - 1) // (h - 1)] = 1  # Diagonal
        elif letter == "O":
            grid[1 : h - 1, 0] = 1  # Left side
            grid[1 : h - 1, w - 1] = 1  # Right side
            grid[0, 1 : w - 1] = 1  # Top
            grid[h - 1, 1 : w - 1] = 1  # Bottom
        elif letter == "P":
            grid[:, 0] = 1  # Left side
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[1 : h // 2, w - 1] = 1  # Top right
        elif letter == "Q":
            grid[1 : h - 1, 0] = 1  # Left side
            grid[1 : h - 1, w - 1] = 1  # Right side
            grid[0, 1 : w - 1] = 1  # Top
            grid[h - 1, 1 : w - 1] = 1  # Bottom
            grid[h - 2 : h, w - 2 : w] = 1  # Tail
        elif letter == "R":
            grid[:, 0] = 1  # Left side
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[1 : h // 2, w - 1] = 1  # Top right
            for i in range(h // 2, h):
                j = (i - h // 2) * (w - 1) // ((h - 1) - h // 2)
                if j < w:
                    grid[i, j] = 1  # Diagonal
        elif letter == "S":
            grid[0, :] = 1  # Top
            grid[h // 2, :] = 1  # Middle
            grid[h - 1, :] = 1  # Bottom
            grid[1 : h // 2, 0] = 1  # Top left
            grid[h // 2 + 1 : h - 1, w - 1] = 1  # Bottom right
        elif letter == "T":
            grid[0, :] = 1  # Top
            grid[:, w // 2] = 1  # Middle vertical
        elif letter == "U":
            grid[: h - 1, 0] = 1  # Left side
            grid[: h - 1, w - 1] = 1  # Right side
            grid[h - 1, 1 : w - 1] = 1  # Bottom
        elif letter == "V":
            for i in range(h - 1):
                grid[i, i * (w - 1) // (h - 1)] = 1  # Left diagonal
                grid[i, w - 1 - i * (w - 1) // (h - 1)] = 1  # Right diagonal
            grid[h - 1, w // 2] = 1  # Bottom point
        elif letter == "W":
            grid[:, 0] = 1  # Left side
            grid[:, w - 1] = 1  # Right side
            grid[h // 2 :, w // 2] = 1  # Middle bottom
        elif letter == "X":
            for i in range(h):
                grid[i, i * (w - 1) // (h - 1)] = 1  # Main diagonal
                grid[i, w - 1 - i * (w - 1) // (h - 1)] = 1  # Counter diagonal
        elif letter == "Y":
            for i in range(h // 2):
                grid[i, i * (w - 1) // (h - 1)] = 1  # Left diagonal
                grid[i, w - 1 - i * (w - 1) // (h - 1)] = 1  # Right diagonal
            grid[h // 2 :, w // 2] = 1  # Bottom vertical
        elif letter == "Z":
            grid[0, :] = 1  # Top
            grid[h - 1, :] = 1  # Bottom
            for i in range(h):
                grid[i, w - 1 - i * (w - 1) // (h - 1)] = 1  # Diagonal

        return grid

    def generate_pattern(self, char, grid_size=(10, 10)):
        if not char:
            return np.zeros(grid_size)

        char = char.upper()
        if char.isdigit():
            pattern = self._get_digit_pattern(char)
        elif char.isalpha():
            pattern = self._get_letter_pattern(char)
        else:
            return np.zeros(grid_size)

        result = np.zeros(grid_size)

        # Calculate position to center the character
        start_row = (grid_size[0] - self.font_size[0]) // 2
        start_col = (grid_size[1] - self.font_size[1]) // 2

        # Place the pattern in the center of the grid
        result[
            start_row : start_row + self.font_size[0],
            start_col : start_col + self.font_size[1],
        ] = pattern

        return result


class PatternLibraryWidget(QGroupBox):
    patternSelected = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__("Pattern Generator")
        self.text_generator = TextPatternGenerator()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Text pattern section
        text_group = QGroupBox("Text Pattern")
        text_layout = QHBoxLayout()

        # Add text input
        self.text_input = QLineEdit()
        self.text_input.setMaxLength(1)  # Only one character at a time
        self.text_input.returnPressed.connect(
            self.onTextPatternSelected
        )  # Add Enter key handler
        text_layout.addWidget(QLabel("Character:"))
        text_layout.addWidget(self.text_input)

        # Add generate button
        generate_text_btn = QPushButton("Generate")
        generate_text_btn.clicked.connect(self.onTextPatternSelected)
        text_layout.addWidget(generate_text_btn)

        text_group.setLayout(text_layout)
        layout.addWidget(text_group)

        # Add Random Grid button
        random_btn = QPushButton("Random Grid")
        random_btn.clicked.connect(lambda: self.window().generateRandomGrid())
        layout.addWidget(random_btn)

        self.setLayout(layout)

    def onTextPatternSelected(self):
        char = self.text_input.text().upper()
        if char:
            pattern = self.text_generator.generate_pattern(char)
            self.patternSelected.emit(pattern)
            # Signal the main window to update the result
            main_window = self.window()
            if main_window:
                main_window.updateResult()
            self.text_input.clear()  # Clear the input after generating


class MorphologicalGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Morphological Operations")

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()

        # Left panel (input)
        left_panel = QWidget()
        left_layout = QVBoxLayout()

        # Add input grid label and grid
        left_layout.addWidget(QLabel("Input Grid (Click to Toggle)"))
        self.left_grid = EnhancedGridWidget(rows=10, cols=10, editable=True)
        self.left_grid.gridChanged.connect(self.updateResult)
        left_layout.addWidget(self.left_grid)

        # Add explanation widget
        self.explanation = OperationExplanationWidget()
        left_layout.addWidget(self.explanation)

        left_panel.setLayout(left_layout)

        # Middle panel (controls)
        middle_panel = QWidget()
        middle_layout = QVBoxLayout()

        # Operation selector
        middle_layout.addWidget(QLabel("Operation:"))
        self.operation_combo = QComboBox()
        self.operation_combo.addItems(["Erosion", "Dilation", "Opening", "Closing"])
        self.operation_combo.currentTextChanged.connect(self.onOperationChanged)
        middle_layout.addWidget(self.operation_combo)

        # Structuring element
        middle_layout.addWidget(QLabel("Structuring Element (Click to Edit):"))
        self.struct_element = EnhancedGridWidget(
            rows=3, cols=3, editable=True, button_size=20
        )
        self.struct_element.gridChanged.connect(self.updateResult)
        struct_grid = np.ones((3, 3))
        self.struct_element.setGrid(struct_grid)
        middle_layout.addWidget(self.struct_element)

        # Pattern library
        self.pattern_library = PatternLibraryWidget()
        self.pattern_library.patternSelected.connect(self.left_grid.setGrid)
        middle_layout.addWidget(self.pattern_library)

        middle_panel.setLayout(middle_layout)

        # Right panel (result)
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Result"))
        self.right_grid = EnhancedGridWidget(rows=10, cols=10, editable=False)
        right_layout.addWidget(self.right_grid)
        right_panel.setLayout(right_layout)

        # Add all panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(middle_panel)
        main_layout.addWidget(right_panel)

        main_widget.setLayout(main_layout)
        self.generateRandomGrid()

    def generateRandomGrid(self):
        rows = cols = 10  # Fixed size
        random_grid = np.random.choice([0, 1], size=(rows, cols), p=[0.7, 0.3])
        self.left_grid.setGrid(random_grid)
        self.updateResult()

    def onOperationChanged(self, operation):
        self.explanation.updateExplanation(operation)
        self.updateResult()

    def updateResult(self):
        input_grid = self.left_grid.getGrid()
        structure = self.struct_element.getGrid()
        operation = self.operation_combo.currentText()

        # Direct result without animation
        result = self.applyOperation(input_grid, structure, operation)
        self.right_grid.setGrid(result)
        self.right_grid.update()  # Force UI refresh

    def applyOperation(self, input_grid, structure, operation):
        if operation == "Erosion":
            return ndimage.binary_erosion(input_grid, structure=structure)
        elif operation == "Dilation":
            return ndimage.binary_dilation(input_grid, structure=structure)
        elif operation == "Opening":
            return ndimage.binary_opening(input_grid, structure=structure)
        elif operation == "Closing":
            return ndimage.binary_closing(input_grid, structure=structure)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    morphological_gui = MorphologicalGUI()
    morphological_gui.show()
    sys.exit(app.exec_())
