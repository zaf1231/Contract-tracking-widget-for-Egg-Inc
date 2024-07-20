from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QToolButton
from PyQt5.QtGui import QPainter, QPixmap, QColor, QBrush, QRadialGradient, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRectF, QPointF, QTimer, QSize
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import sys
import os

path = "C:/Users/.../Coop widget 1.0 release"  # CHANGE THIS TO YOUR OWN FILE PATH
EID = "EIXXXXXXXXXXXX"  # PUT YOUR OWN PLAYER ID HERE
scaleSize = 130  # Change this number to change the size of the widget
x_position = 100 # CHANGE THIS TO THE X POSITION YOU WANT
y_position = 100 # CHANGE THIS TO THE Y POSITION YOU WANT

class RingProgressBar(QWidget):
    def __init__(self, parent=None):
        super(RingProgressBar, self).__init__(parent)
        self.percentage_complete = 0
        self.percentage_predicted = 0
        self.slot_text = ""
        self.setFixedSize(scaleSize, scaleSize)
        self.picture = None  # Initialize with None
        self.setAttribute(Qt.WA_TranslucentBackground)  # Set widget background as translucent

    def setPicture(self, picture_path):
        self.picture = QPixmap(picture_path).scaled(round(scaleSize / 2), round(scaleSize / 2)) if picture_path else None
        self.repaint()

    def setPercentageComplete(self, percentage):
        self.percentage_complete = percentage
        self.repaint()

    def setPercentagePredicted(self, percentage):
        self.percentage_predicted = percentage
        self.repaint()

    def setSlotText(self, text):
        self.slot_text = text
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # Transparent background
        painter.fillRect(event.rect(), Qt.transparent)

        if self.picture:
            picture_rect = self.picture.rect()
            picture_center = QPointF(width / 2.0, height / 2.0 - 8)
            picture_rect.moveCenter(picture_center.toPoint())
            painter.drawPixmap(picture_rect, self.picture)

        # Outer gray gradient circle
        outer_gradient = QRadialGradient(width / 2.0, height / 2.0, width / 2.0)
        outer_gradient.setColorAt(1, QColor(100, 100, 100, 100))
        outer_gradient.setColorAt(0.87, QColor(100, 100, 100, 100))
        outer_gradient.setColorAt(0.82, QColor(0, 0, 0, 0))
        outer_gradient.setColorAt(0, QColor(0, 0, 0, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(outer_gradient))
        painter.drawEllipse(0, 0, width, height)

        # Inner progress gradient arc (predicted)
        inner_gradient_predicted = QRadialGradient(width / 2.0, height / 2.0, width / 2.0)
        inner_gradient_predicted.setColorAt(1, QColor(167, 243, 208, 255))
        inner_gradient_predicted.setColorAt(0.87, QColor(167, 243, 208, 255))
        inner_gradient_predicted.setColorAt(0.82, QColor(0, 0, 0, 0))
        inner_gradient_predicted.setColorAt(0, QColor(0, 0, 0, 0))

        painter.setBrush(QBrush(inner_gradient_predicted))

        progress_span_predicted = int((360 * self.percentage_predicted) / 100)
        start_angle = 270 * 16

        painter.drawPie(QRectF(0, 0, width, height), start_angle, -progress_span_predicted * 16)

        # Inner progress gradient arc (complete)
        inner_gradient_complete = QRadialGradient(width / 2.0, height / 2.0, width / 2.0)
        inner_gradient_complete.setColorAt(1, QColor(15, 178, 123, 255))
        inner_gradient_complete.setColorAt(0.87, QColor(15, 178, 123, 255))
        inner_gradient_complete.setColorAt(0.82, QColor(0, 0, 0, 0))
        inner_gradient_complete.setColorAt(0, QColor(0, 0, 0, 0))

        painter.setBrush(QBrush(inner_gradient_complete))

        progress_span_complete = int((360 * self.percentage_complete) / 100)

        painter.drawPie(QRectF(0, 0, width, height), start_angle, -progress_span_complete * 16)

        # Draw slot text
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPointSize(round(scaleSize / 18))
        painter.setFont(font)
        text_rect = QRectF(0, height - 53/150 * scaleSize, width, 20)
        painter.drawText(text_rect, Qt.AlignCenter, self.slot_text)

        # Draw percentages only if slot is active
        if self.percentage_predicted > 0:
            font.setPointSize(round(scaleSize / 22))
            painter.setFont(font)
            painter.drawText(QRectF(0, height - 35/150 * scaleSize, width + 35/150 * scaleSize, 10), Qt.AlignCenter, f"P:{round(self.percentage_predicted)}%")

        if self.percentage_complete > 0:
            font.setPointSize(round(scaleSize / 22))
            painter.setFont(font)
            painter.drawText(QRectF(0, height - 35/150 * scaleSize, width - 35/150 * scaleSize, 10), Qt.AlignCenter, f"C:{round(self.percentage_complete)}%")



class CoopProgressWidget(QWidget):
    def __init__(self):
        super(CoopProgressWidget, self).__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint)  # Set to stay on bottom
        self.setAttribute(Qt.WA_TranslucentBackground)  # Set widget background as translucent
        self.draggable = True
        self.offset = QPoint()
        self.init_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)  # Connect timer timeout to refresh method
        self.timer.start(1800000)  # Start timer with 30 min interval

    def init_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(1)  # Adjust spacing between widgets as needed

        positions = [(i, j) for i in range(2) for j in range(2)]
        self.progress_widgets = []

        for pos in positions:
            progress_widget = RingProgressBar(self)
            layout.addWidget(progress_widget, *pos)
            self.progress_widgets.append(progress_widget)

        self.setLayout(layout)

        # Increase the widget size to accommodate the buttons
        self.setFixedSize(scaleSize * 2 + 60, scaleSize * 2 + 60)  # Adjust size as needed

        # Function to create buttons with hover effects
        def create_button(icon_path, hover_icon_path, x, y, size):
            button = QToolButton(self)
            icon_abs_path = os.path.join(path, icon_path)
            hover_icon_abs_path = os.path.join(path, hover_icon_path)

            button.setIcon(QIcon(icon_abs_path))
            button.setIconSize(QSize(size, size))
            button.setStyleSheet("""
                QToolButton {
                    border: none;
                    background: none;
                }
            """)

            button.installEventFilter(self)
            button.setProperty('hoverIcon', QIcon(hover_icon_abs_path))
            button.setProperty('defaultIcon', QIcon(icon_abs_path))
            button.setIconSize(QSize(size, size))
            button.move(x, y)
            button.show()
            return button


        # Add close button
        self.close_button = create_button("img/Close.png", "img/Close hover.png", scaleSize * 2, 30, 20)
        self.close_button.clicked.connect(self.close)

        # Add refresh button
        self.refresh_button = create_button("img/Refresh.png", "img/Refresh hover.png", scaleSize * 2, 60, 20)
        self.refresh_button.clicked.connect(self.refresh)

        # Add wasmegg button
        self.wasmegg_button = create_button("img/UI.png", "img/UI hover.png", scaleSize * 2, 90, 20)
        self.wasmegg_button.clicked.connect(self.handle_wasmegg_button_click)  # Connect to your handler


    def eventFilter(self, obj, event):
        if isinstance(obj, QToolButton):
            if event.type() == event.Enter:
                obj.setIcon(obj.property('hoverIcon'))
            elif event.type() == event.Leave:
                obj.setIcon(obj.property('defaultIcon'))
        return super(CoopProgressWidget, self).eventFilter(obj, event)

    def setProgress(self, slot_index, complete_percentage, predicted_percentage):
        if slot_index < len(self.progress_widgets):
            self.progress_widgets[slot_index].setPercentageComplete(complete_percentage)
            self.progress_widgets[slot_index].setPercentagePredicted(predicted_percentage)

    def setPicture(self, slot_index, picture_path):
        if slot_index < len(self.progress_widgets):
            self.progress_widgets[slot_index].setPicture(picture_path)

    def setSlotText(self, slot_index, text):
        if slot_index < len(self.progress_widgets):
            self.progress_widgets[slot_index].setSlotText(text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.draggable:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.draggable:
            self.move(self.pos() + event.pos() - self.offset)

    def mouseReleaseEvent(self, event):
        pass  # You can add functionality here if needed

    def refresh(self):
        for widget in self.progress_widgets:
            widget.setPercentageComplete(0)  # Reset all widgets to 0% before refreshing
        scraper.scrape_specific_text()  # Trigger web scraping operation here

    def handle_wasmegg_button_click(self):
        # Define what should happen when wasmegg button is clicked
        print("Wasmegg button clicked!")
        # Add your logic here




class WebScraper:
    def __init__(self):
        self.coop_progress_widget = None
        self.load_button_clicked = False
        self.driver = None

    def connect_gui(self, gui):
        self.coop_progress_widget = gui

    def start_driver(self):
        options = webdriver.ChromeOptions()
        #options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        self.driver = webdriver.Chrome(options=options)
        self.driver.get('https://eicoop-carpet.netlify.app/')
        print("WebDriver started and page loaded.")

    def navigate_to_page(self):
        if not self.driver:
            self.start_driver()
        self.driver.get('https://eicoop-carpet.netlify.app/')
        print("Navigated to the page.")

    def find_elements_with_retry(self, by, value, retries=3, delay=1):
        for i in range(retries):
            try:
                elements = self.driver.find_elements(by, value)
                if elements:
                    return elements
            except StaleElementReferenceException:
                time.sleep(delay)
        return []

    def scrape_specific_text(self):
        try:
            self.navigate_to_page()
            print("Finding elements after navigating...")

            input_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "user_id"))
            )

            input_field.clear()  # Clear any existing text in the input field
            input_field.send_keys(EID)
            print(f"Entered EID: {EID}")

            load_button_xpath = "//button[contains(@class, 'bg-blue-600')]"
            load_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, load_button_xpath))
            )
            load_button.click()
            self.load_button_clicked = True
            print("Clicked the load button.")

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[@class='text-green-500']"))
            )

            try:
                no_contract_message = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'No active contract found in your save. Check back when you have one!')]"))
                )
                print("There are no active contracts.")
                return
            except TimeoutException:
                print("No 'No active contract' message found, continuing to extract slot information.")
                pass

            # Find slots with retry mechanism
            slots = self.find_elements_with_retry(By.XPATH, "//span[@class='active:duration-0 cursor-pointer select-none active:text-green-500 dark:active:text-green-500 text-gray-900 dark:text-gray-100 mr-0.5']")
            print(f"Found {len(slots)} slots.")

            for i, slot in enumerate(slots, start=1):
                slot_text = slot.text
                self.coop_progress_widget.setSlotText(i - 1, slot_text)
                print(f"Slot {i} text: {slot_text}")

                # Fetching image name
                image_name_xpath = f"//*[@id='app']/div[1]/div/main/div[{i + 2}]/div/div[1]/div/div[1]/h2/picture/img"
                try:
                    image_element = self.find_elements_with_retry(By.XPATH, image_name_xpath)[0]
                    image_name = image_element.get_attribute("src").split("/")[-1]
                    print(f"Image Name for Slot {i}: {image_name}")

                    # Determine if slot is inactive
                    is_inactive = "inactive" in slot.get_attribute("class")

                    # Set the picture for the corresponding slot
                    if is_inactive:
                        self.coop_progress_widget.setPicture(i - 1, "")
                    else:
                        self.coop_progress_widget.setPicture(i - 1, path + "/img/" + image_name)
                except IndexError:
                    print(f"Image Name for Slot {i}: Not found")
                    continue
                except NoSuchElementException:
                    print(f"Image Name for Slot {i}: Element not found")
                    continue

                percentage_complete_xpath = f"//*[@id='app']/div[1]/div/main/div[{i + 2}]/div/div[2]/div/div[1]/div[4]"
                percentage_predicted_xpath = f"//*[@id='app']/div[1]/div/main/div[{i + 2}]/div/div[2]/div/div[1]/div[2]"

                try:
                    percentage_complete_element = self.find_elements_with_retry(By.XPATH, percentage_complete_xpath)[0]
                    percentage_complete_text = percentage_complete_element.get_attribute("style")
                    percentage_complete_value = float(percentage_complete_text.split("width: ")[-1].replace("%;", ""))
                    print(f"Percentage Complete for Slot {i}: {percentage_complete_value}%")
                except IndexError:
                    print(f"Percentage Complete for Slot {i}: 0%")
                    continue
                except NoSuchElementException:
                    print(f"No percentage complete information found for Slot {i}. Element not found.")
                    continue

                try:
                    percentage_predicted_element = self.find_elements_with_retry(By.XPATH, percentage_predicted_xpath)[0]
                    if "bg-gray-200 absolute" in percentage_predicted_element.get_attribute("outerHTML"):
                        percentage_predicted_value = 0
                        print(f"Percentage Predicted for Slot {i}: 0%")
                    else:
                        percentage_predicted_text = percentage_predicted_element.get_attribute("style")
                        percentage_predicted_value = float(percentage_predicted_text.split("width: ")[-1].replace("%;", ""))
                        print(f"Percentage Predicted for Slot {i}: {percentage_predicted_value}%")
                except IndexError:
                    print(f"Percentage Predicted for Slot {i}: 0%")
                    continue
                except NoSuchElementException:
                    print(f"No percentage predicted information found for Slot {i}. Element not found.")
                    continue

                self.coop_progress_widget.setProgress(i - 1, percentage_complete_value, percentage_predicted_value)

        except TimeoutException:
            print("Timeout occurred. Element not found.")
        except Exception as e:
            print("Error:", e)

    def run(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)

    gui = CoopProgressWidget()
    scraper = WebScraper()
    scraper.connect_gui(gui)

    # Adjust the initial position here
    gui.move(x_position, y_position)  # Replace with the desired x, y coordinates

    gui.show()
    scraper.scrape_specific_text()  # Start scraping on application launch

    sys.exit(app.exec_())