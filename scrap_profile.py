from math import e
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.action_chains import ActionChains
import time
import datetime;

def login(email,password):
    driver = webdriver.Chrome()  # Replace with the appropriate WebDriver for your browser
    driver.get("https://www.facebook.com")
    driver.maximize_window()
    email_input = driver.find_element(By.ID, "email")
    password_input = driver.find_element(By.ID, "pass")
    login_button = driver.find_element(By.NAME, "login")

    email_input.send_keys(email)
    password_input.send_keys(password)
    login_button.click()
    return driver

def scrap_user_html_content(html_content):
  # try:
  soup = BeautifulSoup(html_content, 'html.parser')

  # Find elements by class name and extract data
  elements_with_class = soup.find_all(attrs={'data-ad-preview': 'message'})
  post_msg = elements_with_class[0].text

  ##############################Post Content######################################
  print("Page Post ",post_msg)

  # Find elements by attribute and extract data
  elements_with_attribute = soup.find_all(attrs={'role': 'article'})

  href_link = list()
  name = list()
  comment = list()
  postMsg = list() 
  for element in elements_with_attribute:

      ##############################Post Comment######################################
      print("Comment of post in popup",element.text)

      anchor_tags = element.find_all('a')
      for anchor in anchor_tags:

          ##############################Comment User Name #############################
          text = anchor.text

          ##############################Profile URL #############################
          href = anchor['href']

          if len(text.replace(" ", ""))>3:
              href_link.append(href)
              name.append(text)
              
              ##############################Fileter Out Comment #############################
              commentText = element.text
              Commentonmessage = commentText.lower()
              Commentonmessage = Commentonmessage.replace(text.lower(),'')
              Commentonmessage = Commentonmessage.replace('Follow'.lower(),'')
              Commentonmessage = Commentonmessage.replace('LikeReply'.lower(),'')
              Commentonmessage = Commentonmessage.replace('Top fan'.lower(),'')
              
              comment.append(Commentonmessage)
              postMsg.append(post_msg)
              print(f"Anchor Text: {text}")
              print(f"Href Tag:{href}")

  data = {
    "Post":postMsg,  
    "Comment": comment,
    "Name": name,
    "Href": href_link
  }
  ct = datetime.datetime.now()
  ts = ct.timestamp()
  #load data into a DataFrame object:
  #df = pd.DataFrame(data)

  df = pd.DataFrame(data)
  # appending the data of df after the data of demo1.xlsx
  with pd.ExcelWriter("BJP4Delhi.xlsx",mode="a",engine="openpyxl",if_sheet_exists="overlay") as writer:
    df.to_excel(writer, sheet_name="Sheet1",header=None, startrow=writer.sheets["Sheet1"].max_row,index=False)
    print("Data Inserted into Excel Sheet")
  #df.to_excel('data/akhilesh_1696247468.997519.xlsx', index=False, mode='a', header=False)
  #df.to_excel(f"data/akhilesh_{ts}.xlsx", index=False)
  print(df)
  # except Exception as error:
  #    sleep(3)
  #    print("scrap_user_html_content:", error) # An error occurred: name 'x' is not defined
  #    pass 


def scrap_popup_html(driver,pageName):
    driver.get(pageName)
    wait = WebDriverWait(driver, 20)

    # Filter the span elements to only include those which contain "View more comments".
    view_more_comments_span_elements = []
    i=0
    while i<1000:
        i+=1
        sleep(3)
        #span_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'View more comments')]")
        span_elements = driver.find_elements(By.XPATH, "//div[@class='x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z']")
        sleep(3)
        print('Post Content',span_elements[0].text)

        for span_element in span_elements:
          try:
              ############################ Click On View More Comments ############################
              #sleep(3)
              #print("Post Content Print=>",span_element.text)
              # view_more_comments_span = span_element.find_element(By.XPATH, "//span[contains(text(), 'View more comments')]")
              
              wait = WebDriverWait(driver, 10)
              view_more_comments_span = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'View more comments')]")))

              if view_more_comments_span:
                  action = ActionChains(driver)
                  action.move_to_element(view_more_comments_span).click().perform()
              else:
                  pass
              wait = WebDriverWait(driver, 5)
              wait.until(lambda driver: driver.find_element(By.XPATH, "//div[@role='dialog' and @aria-labelledby]"))
              #sleep(5)                          
              popup_element = driver.find_element(By.XPATH, "//div[@role='dialog' and @aria-labelledby]")
              print("Parent popupd",popup_element.text)
              outer_html = popup_element.get_attribute("outerHTML")
              print("=====================")
              print(outer_html)
              scrap_user_html_content(outer_html)

              sleep(2)
              backButton = driver.find_elements(By.XPATH, "//div[@aria-label='Close']")
              action = ActionChains(driver)
              action.move_to_element(backButton[0]).click().perform()
                ################################ Close Popup ########################################
                #popup_element = driver.find_element(By.XPATH, "//div[@aria-label='Close']")
                #popup_element.click()
                #sleep(2)
          except Exception as error:
            print("scrap_popup_html:", error) # An error occurred: name 'x' is not defined
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        sleep(3)
        

driver = login('gmailId','password')

# Wait for the element to be present
wait = WebDriverWait(driver, 20)
sleep(4)
scrap_popup_html(driver,"https://www.facebook.com/BJP4Delhi")

