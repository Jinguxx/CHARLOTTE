
import json
import csv
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import cv2
import numpy as np
import socket
from urllib.parse import urlparse
import requests
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser
import time
import os
import shutil
import math
import pyautogui
from datetime import datetime  # Import the datetime module


def init_driver():
    # Set up Selenium with Chrome WebDriver
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Add this line for headless mode
    chrome_options.add_argument('--disable-gpu')  # Add this line to disable GPU (necessary for headless mode on some platforms)
    driver_path = "/Users/jingu/Desktop/CHARLOTTE/chromedriver"  # Replace with the path to your ChromeDriver executable
    return webdriver.Chrome(service=Service(driver_path), options=chrome_options)


def calculate_relative_luminance(R, G, B):
    def sRGB_to_linear(channel):
        if channel <= 0.04045:
            return channel / 12.92
        else:
            return ((channel + 0.055) / 1.055) ** 2.4

    R_linear = sRGB_to_linear(R / 255.0)
    G_linear = sRGB_to_linear(G / 255.0)
    B_linear = sRGB_to_linear(B / 255.0)

    return 0.2126 * R_linear + 0.7152 * G_linear + 0.0722 * B_linear


def calculate_contrast_ratio(image_path):
    
    image = image_path.convert("RGB")
    
    # Convert the image to a numpy array for OpenCV processing
    img_np = np.array(image)

    # Convert the image to grayscale for contour detection
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

    # Threshold the image to create a binary image (black and white)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

    # Find contours (edges) in the image
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) == 0:
        print("No letters found in the image.")
        return 0.0

    # Assuming the letter with the largest contour is the desired one
    largest_contour = max(contours, key=cv2.contourArea)

    # Get the bounding box of the letter
    x, y, w, h = cv2.boundingRect(largest_contour)

    # Get the center pixel of the letter
    center_x, center_y = x + w // 2, y + h // 2

    # Assuming the background pixel is immediately next to the letter (adjust as needed)
    background_x, background_y = center_x + 1, center_y

    # Get the RGB values of the letter and background pixels
    letter_pixel = img_np[center_y, center_x]
    background_pixel = img_np[background_y, background_x]

    letter_luminance = calculate_relative_luminance(*letter_pixel)
    background_luminance = calculate_relative_luminance(*background_pixel)

    L1 = max(letter_luminance, background_luminance)
    L2 = min(letter_luminance, background_luminance)

    contrast_ratio = (L1 + 0.05) / (L2 + 0.05)

    return contrast_ratio


def take_screenshot(driver, url):
    
    # Create a folder for screenshots if it doesn't exist
    parsed_url = urlparse(url)
    folder = parsed_url.hostname
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    width = 1920
    height = driver.execute_script("return Math.max(document.body.scrollHeight,document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")
    
    driver.set_window_size(width, height)
    
    time.sleep(5)
    
    # Save the full screenshot with the URL name and date in the specified folder
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(folder, f"{url.replace('/', '_').replace(':', '')}_{current_datetime}.png")
    driver.save_screenshot(filename)
    
    # Calculate contrast ratio
    screenshot = Image.open(filename)
    contrast_ratio = calculate_contrast_ratio(screenshot)

    if contrast_ratio is not None:  # Check if contrast_ratio is not None before comparing
        print("Contrast Ratio:", contrast_ratio)

        if contrast_ratio >= 4.5:
            print("Contrast ratio is equal to or greater than 4.5:1.\n")
        else:
            print("Contrast ratio is less than 4.5:1.\n")
    else:
        print("Unable to calculate contrast ratio.\n")



def scrape_website(url):
    try:
        # Initialize the driver
        driver = init_driver()

        # Adding a delay of 2 seconds before accessing the URL
        time.sleep(5)

        driver.get(url)

        # Add a delay after the page load (adjust the sleep time based on your page load time)
        time.sleep(20)

        # Get the current date and time
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        parsed_url = urlparse(url)
        host = parsed_url.hostname

        try:
            # getting the IP address using socket.gethostbyname() method
            ip_address = socket.gethostbyname(host)
            
        except socket.gaierror:
            # Handle the gaierror gracefully
            print(f"Error: Unable to resolve IP address for hostname '{host}'.")
            ip_address = "N/A"

        # Extract the URL and IP address from the website
        website_url = driver.current_url

        # Take a screenshot and save it to the folder with the current or previous URL as the folder name
        take_screenshot(driver, website_url)

        driver.quit()

        return {"hostname": host, "url": website_url, "ip_address": ip_address, "scraped_date": current_date}
    
    except Exception as e:
        # Handle other exceptions that might occur during web scraping
        print(f"Error: An error occurred while scraping '{url}': {str(e)}\n")
        return None


def scrape_website_csv(url):
    # Initialize the driver
    driver = init_driver()
    
    # Adding a delay of 2 seconds before accessing the URL
    time.sleep(5)
    
    driver.get(url)
    
    # Add a delay after the page load (adjust the sleep time based on your page load time)
    time.sleep(20)
    
    parsed_url = urlparse(url)
    host = parsed_url.hostname
    
    ## getting the IP address using socket.gethostbyname() method
    ip_address = socket.gethostbyname(host)

    # Extract the URL and IP address from the website
    website_url = driver.current_url
    
    # Take a screenshot and save it to a folder with the URL name
    screenshot_folder = "website_screenshots"
    take_screenshot(driver, website_url, screenshot_folder)
    
    driver.quit()

    return host,website_url,ip_address


def save_to_csv(data, filename):
    # Save the scraped data to a CSV file
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)


def save_to_json(data, filename):
    # Save the scraped data to a JSON file
    with open(filename, 'a') as file:
        json.dump(data, file)
        file.write('\n')


def main():
    
    user_agent = "CHARLOTTE"  # Replace with a unique user agent string for your bot
    
    print("\n")
    print("    /\\  .-'''-.  /\\")
    print("   //\\/  ,,,  \//\\")
    print("   |/\| ,;;;;;, |/\|")
    print("   //\\\;-'''-;///\\")
    print("  //  \/   .   \/  \\")
    print(" (| ,-_| \ | / |_-, |)")
    print("  //`__\.-.-./__`\\")
    print(" // /.-(() ())-.\ \\")
    print("(\ |)   '---'   (| /)")
    print(" ` (|           |) `")
    print("  \)           (/")
    print(user_agent)
    print("\n")

        
    # Replace with the desired filename for the output JSON file
    output_json_file = "charlotte_visted.json"

    # Replace with the path to your input CSV file containing URLs
    url_input = input("Enter file with URL for website (type 'exit' to quit): ")

    # Read the CSV file and loop through each URL to scrape the websites
    with open(url_input, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            url_input = row[0]
            print("Scraping: ",url_input)

            # Check if the URL is empty or "exit" to break the loop
            if url_input.lower() == 'exit' or not url_input:
                print("Exiting the loop.")
                break

            scraped_data = scrape_website(url_input)

            # Save the data to JSON
            save_to_json(scraped_data, output_json_file)
        

if __name__ == "__main__":
    main()
    
    
    
    
    
