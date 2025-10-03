from PIL import Image, ImageDraw, ImageFont
import card_load
import random
import math
import cv2
import numpy as np

class ImageGen:

    def __init__(self, question_path):
        self.res1 = self.cm_to_resolution(8.9, 5.7, 300)
        self.res2 = self.cm_to_resolution(9.2, 5.9, 300)
        self.res3 = self.cm_to_resolution(8.8, 6.3, 300)

        self.res_list = [self.res1, self.res2, self.res3]

        self.img_path ="picture.png"

        self.resolution = self.cm_to_resolution(8.9, 5.7, 300)

        self.card_list = CardGenerator.load_cards_from_file(question_path)
        self.get_boxes()

    def get_boxes(self):
        self.colors = {"6":(np.array([150,200, 130]),np.array([180, 255, 160])),
                       "2":(np.array([220, 110, 100]),np.array([255, 150, 130])),
                       "3":(np.array([240, 180, 130]),np.array([255, 210, 150])),
                       "4":(np.array([240, 230, 140]),np.array([255, 255, 170])),
                       "area":(np.array([140,160,180]),np.array([170,190,200])),
                       "question":(np.array([80, 160, 180]),np.array([100, 190, 200])),
                       }
        self.boxes = {}
        for key in self.colors.keys():
            self.boxes[key] = self.get_box(self.colors[key][0],self.colors[key][1])



    def cm_to_resolution(self,x,y,dpi):
        return (round(x*0.3937008*dpi), round(y*0.3937008*dpi))

    def draw_cards(self, path):

        for i,card in enumerate(self.card_list):
            self.img = Image.open(self.img_path)
            self.draw = ImageDraw.Draw(self.img)
            self.width, self.height = self.img.size
            self.draw_question(card)
            self.draw_subject(card)
            self.draw_answers(card)
            self.img.save(f"{path}/{i}.png")


    def draw_subject(self, card=None, text=None, coordinates=None, font=None):
        self.draw_text_in_box(self.boxes["area"][0], card.kategori, padding= 3)


    def draw_answers(self, card):
        self.draw_text_in_box(self.boxes["6"][0], card.poäng_gränser_dict["6"])

        self.draw_text_in_box(self.boxes["2"][0], card.poäng_gränser_dict["2_l"])
        self.draw_text_in_box(self.boxes["2"][1], card.poäng_gränser_dict["2_ö"])

        self.draw_text_in_box(self.boxes["3"][0], card.poäng_gränser_dict["3_l"])
        self.draw_text_in_box(self.boxes["3"][1], card.poäng_gränser_dict["3_ö"])

        self.draw_text_in_box(self.boxes["4"][0], card.poäng_gränser_dict["4_l"])
        self.draw_text_in_box(self.boxes["4"][1], card.poäng_gränser_dict["4_ö"])




    def draw_question(self,card):
        self.draw_text_in_box(self.boxes["question"][0], card.fråga, padding= 10)
    def get_box(self, lower_color, upper_color):
        # --- 2. Load and Process the Image ---
        # Load the image from your file path
        image = cv2.imread(self.img_path)
        if image is None:
            print("Error: Image not found.")
        else:
            # Convert the image from BGR (OpenCV's default) to HSV
            hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Create a mask that isolates the blue color
            mask = cv2.inRange(hsv_image, lower_color, upper_color)

            # Optional: Clean up the mask with morphological operations
            # This helps remove small noise or fill in small holes
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)

            # --- 3. Find Contours and the Bounding Box ---
            # Find all the contours in the mask
            contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Check if any contours were found
            box_coords = []
            if len(contours) > 0:
                # Find the largest contour by area, assuming it's our box
                for c in contours:
                    area = cv2.contourArea(c)

                    if area > 50:
                        box_coords.append(cv2.boundingRect(c))

            return box_coords

    def draw_text_in_box(self, box_coords, text, font_path='arial.ttf', padding=2):
        """
        Draws text inside a bounding box, automatically wrapping words and
        finding the optimal font size.

        :param image: PIL Image object.
        :param box_coords: Tuple (x, y, w, h) defining the bounding box.
        :param text: The text string to draw.
        :param font_path: Path to the .ttf font file.
        """

        x, y, w, h = box_coords

        effective_w = w - (2 * padding)
        effective_h = h - (2 * padding)

        if effective_w <= 0 or effective_h <= 0:
            print("Padding is too large for the box size.")
            return

        font_size = effective_h
        font = None
        wrapped_lines = []

        # === Huvudsaklig korrigering börjar här ===

        while font_size > 5:  # Sätt en rimlig minsta storlek
            font = ImageFont.truetype(font_path, font_size)

            # FIX: Beräkna en KONSTANT och pålitlig radhöjd.
            # Vi använder en sträng med både höga och låga bokstäver för att få ett bra mått.
            _, top, _, bottom = font.getbbox('Agy')
            line_height = bottom - top

            # Radbrytning (Word wrapping)
            words = text.split(' ')
            lines = []
            current_line = ''

            for word in words:
                test_line = f'{current_line} {word}'.strip()
                line_width = self.draw.textlength(test_line, font=font)

                if line_width <= effective_w:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            lines.append(current_line)

            # FIX: Använd den konstanta radhöjden för att beräkna totalhöjden.
            total_text_height = len(lines) * line_height

            if total_text_height <= effective_h:
                wrapped_lines = lines
                break
            else:
                font_size -= 1

        if not wrapped_lines:
            print("Texten får inte plats i rutan.")
            return

        # === Slut på huvudsaklig korrigering ===

        # Rita ut texten rad för rad
        # Vi har redan den korrekta totala höjden från loopen ovan.
        total_text_height = len(wrapped_lines) * line_height
        y_start = y + padding + (effective_h - total_text_height) / 2

        current_y = y_start
        for line in wrapped_lines:
            line_width = self.draw.textlength(line, font=font)
            line_x = x + padding + (effective_w - line_width) / 2
            self.draw.text((line_x, current_y), line, font=font, fill="black")
            current_y += line_height


    def img_show(self):
        self.img.show()


creator = ImageGen("fragor.csv")
creator.draw_cards("C:/img")
