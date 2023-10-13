from tokenize import Comment
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from selenium.webdriver.common.action_chains import ActionChains
import re
import phonenumbers
from googletrans import Translator

# Import libraries
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import time

from transformers import BertTokenizer, BertForSequenceClassification
from torch.nn.functional import softmax

#It's is responsible for facebook login, it's taking user name and password as argument 
#Return driver object 
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

#Define function to translate hindi lang to English lang, 
#Return english senetence
def hindToEnglish(sent):
    max_retries=3
    translator = Translator()
    hindi_sentence = sent
    for retry in range(max_retries):
        try:
            english_sentence = translator.translate(hindi_sentence, dest='en').text
            return english_sentence
        except:
            print(f"Translation request timed out ")
            time.sleep(3)  # Wait for a few seconds before retrying
        

    # print(sent)
    # translator = Translator()
    # hindi_sentence = sent
    # english_sentence = translator.translate(hindi_sentence, dest='en').text
    # print(english_sentence)
    # sleep(3)
    # return english_sentence

# Define a function to perform sentiment analysis
def analyze_sentiment(text):

    # Load the pre-trained BERT model and tokenizer
    model_name = "bert-base-uncased"  # You can use different BERT variants
    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertForSequenceClassification.from_pretrained(model_name)

    # Tokenize the input text and convert it to tensor
    inputs = tokenizer(text, padding=True, truncation=True, return_tensors="pt")
    
    # Forward pass through the model
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Get the predicted probabilities
    probabilities = softmax(outputs.logits, dim=1)
    
    # Get the predicted sentiment label (0 for negative, 1 for neutral, 2 for positive)
    predicted_label = torch.argmax(probabilities, dim=1).item()
    
    return predicted_label, probabilities

# Define function to get sentiment
def get_sentiment(text):
  
    # Load pre-trained DistilBERT model and tokenizer
    # Use a smaller DistilBERT model for faster inference
    model_name = "distilbert-base-uncased-finetuned-sst-2-english"
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Tokenize text
    encoded_text = tokenizer.encode_plus(text, return_tensors='pt')

    # Get sentiment prediction 
    output = model(**encoded_text)
    scores = output[0][0].detach().numpy()
    scores = torch.nn.functional.softmax(torch.tensor(scores), dim=0)
    print("dsarsadf saddddddddd",scores)
    # Get sentiment label
    label = 'Positive_'+str(scores[1]) if scores[1] > scores[0] else 'Negative_'+str(scores[0])

    return label

#Define function to scrap profile overview data, It's taking driver and profile URL as parameter
#Return overview data
def scrap_overview(driver,profileName):
    driver.get(profileName)
    wait = WebDriverWait(driver, 20)

    # Find the span element by its text content using JavaScript
    span_text = "About"  # Replace with the actual text you want to click
    js_script = f"var spans = document.querySelectorAll('span'); for (var span of spans) {{ if (span.textContent === '{span_text}') {{ span.click(); }} }}"
    driver.execute_script(js_script)
    sleep(2)

    # Find the span element by its text content using JavaScript
    span_text = "Overview"  # Replace with the actual text you want to click
    js_script = f"var spans = document.querySelectorAll('span'); for (var span of spans) {{ if (span.textContent === '{span_text}') {{ span.click(); }} }}"
    driver.execute_script(js_script)
    sleep(2)

    #Get profile overview data and concatinate those data
    frd_overview = ''
    friendLIst_overview = driver.find_elements(By.XPATH,"//div[@class='x1hq5gj4']")
    for friendMT in friendLIst_overview:
        frd_overview +=friendMT.text+'\n' 
        friendLIst_overview = driver.find_elements(By.XPATH,"//div[@class='x1hq5gj4']")

    friendLIst_overview = driver.find_elements(By.XPATH,"//div[@class='xat24cr']")
    
    for friendMT in friendLIst_overview:
        frd_overview+=frd_overview+friendMT.text+'\n'

    return frd_overview    

#Define function to, Extract city, state, country from overview profile data and return as a disknary 
def extract_lives_in(text):

    #================================ Extract Data from Lives in ====================

    # Define a regular expression pattern to match lines starting with "Lives in"
    pattern = r'^Lives in.*$'
    
    # Use the re.MULTILINE flag to match lines in a multiline text
    matches = re.findall(pattern, text, flags=re.MULTILINE)
    current_state=['delhi','andaman and nicobar islands','chandigarh','puducherry','daman and diu and dadra and nagar haveli','lakshadweep','jammu and kashmir','ladakh','andhra pradesh','assam','arunachal pradesh','bihar','chhattisgarh','gujarat','goa','himachal pradesh','haryana','jharkhand','kerala','karnataka','maharashtra','madhya pradesh','manipur','mizoram','mizoram','nagaland','odisha','punjab','rajasthan','sikkim','tamil nadu','telangana','tripura','west bengal','uttarakhand','uttar pradesh']
    # Extract and return the first match (if any)
    #first index - city
    #second index - state
    #third index - Country
    lives_in = list((" "," "," "))
    lives_from_data = dict()
    if matches:
        filterText = matches[0].replace('Lives in',"")
        livesData = filterText.split(',')
        print("Lived Data",livesData)
        if len(livesData)>2:
            lives_in[0] = livesData[0]
            lives_in[1] = livesData[1]
            lives_in[2] = livesData[2]
        elif len(livesData)==2:
            lives_in[0] = livesData[0]
            Livest = livesData[0].lower()
            if Livest.strip() in current_state:
                lives_in[1] = livesData[0]
                lives_in[0] = ''
            print(livesData[1])
            lives_in[2] = livesData[1]
            stlive = livesData[1].lower()
            if stlive.strip() in current_state:
                lives_in[1] = livesData[1]
                lives_in[2] = ''
            
        elif len(livesData)==1:
            lives_in[0] = livesData[0]

        print("Lives in",lives_in)
    #================================ Extract Data from location =====================

    # Define a regular expression pattern to match lines starting with "Lives in"
    pattern = r'^From.*$'
    
    # Use the re.MULTILINE flag to match lines in a multiline text
    matches = re.findall(pattern, text, flags=re.MULTILINE)
    
    # Extract and return the first match (if any)
    #first index - city
    #second index - state
    #third index - Country
    from_in = list((" "," "," "))
    
    if matches:
        filterText = matches[0].replace('From',"")
        fromData = filterText.split(',')
        print("form data",fromData)
        if len(fromData)==3:
            from_in[0] = fromData[0]
            from_in[1] = fromData[1]
            from_in[2] = fromData[2]
        elif len(fromData)==2:
            from_in[0] = fromData[0]
            st = fromData[0].lower()
            if st.strip() in current_state:
                from_in[1] = fromData[0]
                from_in[0] = ''

            from_in[2] = fromData[1]
            stst = fromData[1].lower()
            if stst.strip() in current_state:
                from_in[1] = fromData[1]
                from_in[2] = ''

            
        elif len(fromData)==1:
            from_in[0] = fromData[0]

    #==========================================Phone Number Get=========================
    phone=''
    for match in phonenumbers.PhoneNumberMatcher(text, "IN"):
        phone = phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164)
    print("pppppppp",phone)
    print("From Data",from_in)
    lives_from_data['cellNo']=phone
    lives_from_data['livesIn']=lives_in
    lives_from_data['fromIn']=from_in
    
    return lives_from_data

#########################################Call Login Function################################
driver = login('Email Id','password')

#########################################Load Excell which is contain post,comment,profile URl################################
excel_file = "output.xlsx"  # Replace with your Excel file path
df = pd.read_excel(excel_file)


post = list()
comment = list()
name = list()
anti_pro = list()
lives_city= list()
lives_state= list()
lives_country= list()
from_city= list()
from_state= list()
from_country= list()
cell_no = list()
sentiment_score = list()
profile_url = list()
# Iterate Through Rows
for index, row in df.iterrows():
    try:
        # Access row data by column name
        posts = row['Post']
        comments = row['Comment']
        comments = comments.replace('·','')
        comments = comments.strip()
        
        match = re.search(r'\d+', comments[::-1])
        if match:
            last_integer = match.group()[::-1]  # Reverse the matched string to get the last integer
            position = len(comments) - match.end()  # Calculate the position of the last integer

            print(f"Last integer: {last_integer}")
            print(f"Position: {position}")
            print(comments[0:position])
            comments = comments[0:position]
        else:
            comments = row['Comment']

        names = row['Name']
        href = row['Href']
        
        post.append(posts)
        name.append(names)
        comment.append(comments)
        profile_url.append(href)
        # Wait for the element to be present
        wait = WebDriverWait(driver, 20)
        sleep(4)
        """
        Sr. Manager at OnSumaye
        Shared with Public

        Studied Informatica at MNNIT, Allahabad, India
        Shared with Your friends

        Lives in Biposi Najafgarh, Uttar Pradesh, India
        Shared with Public

        From Ambedkar Nagar, India
        Shared with Public

        Single
        Shared with Your friends

        085879 96347
        """
        profileOverview = scrap_overview(driver,href)

        #{'cellNo': '+918587996347', 'livesIn': [' Biposi Najafgarh', ' Uttar Pradesh', ' India'], 'fromIn': [' Ambedkar Nagar', ' ', ' India']}
        csc = extract_lives_in(profileOverview)
        print(csc)
        lives_city.append(csc['livesIn'][0] if csc['livesIn'][0] else ' ')
        lives_state.append(csc['livesIn'][1] if csc['livesIn'][1] else ' ')
        lives_country.append(csc['livesIn'][2] if csc['livesIn'][2] else ' ')
        from_city.append(csc['fromIn'][0] if csc['fromIn'][0] else ' ')
        from_state.append(csc['fromIn'][1] if csc['fromIn'][1] else ' ')
        from_country.append(csc['fromIn'][2] if csc['fromIn'][2] else ' ')
        cell_no.append(csc['cellNo'] if csc['cellNo'] else ' ')

        #arg= 'नमस्ते, कैसे हो?'
        if comments:
            comment_english = hindToEnglish(comments)
        else:
            comment_english = 'None'

        if comment_english is None:
            pass

        print('Above Comment')
        predicted_label, probabilities = analyze_sentiment(comment_english)
        print('Below Comment')

        # Define sentiment labels
        sentiment_labels = ["Negative", "Neutral", "Positive"]

        print('Above senti')
        #'Positive' if scores[1] > scores[0] else 'Negative'
        pos_neg_comment = get_sentiment(comment_english)
        print("Below sentiment")

        # Anti Government or Pro Government
        print(pos_neg_comment)
        scoreList = pos_neg_comment.split('_')
        scoreNo = re.findall("\d+\.\d+", scoreList[1])

        print(f"convert string float to float {float(scoreNo[0])}")
        if scoreList[0].strip()=='Positive':
            if float(scoreNo[0]) > 0.9000:
                antPro = 'Pro Government'
            else:
                antPro = 'Anti Government'    
        else:
            if float(scoreNo[0]) > 0.9000:
                antPro = 'Anti Government'
            else:
                antPro = 'Pro Government'

        #antPro = scoreList[0].strip()
        #antPro = sentiment_labels[predicted_label]
        anti_pro.append(antPro)
        
        sentiment_score.append(scoreNo[0])
        #print(f"Row {index + 1}: {post}, {Comment}, {name}")
        

        # initialize data of lists.
        data = {'Post': post,
                'Comments':comment,
                'Names':name,
                'Lives city':lives_city,
                'Lives state' : lives_state,
                'Lives Country' : lives_country,
                'From City':from_city,
                'From State':from_state,
                'From Country':from_country,
                'Cell No':cell_no,
                'Anti/Pro':anti_pro,
                'Sentiment Score':sentiment_score,
                'Profile URL':profile_url
                }
        print(data)
        print("=============")
        # Create DataFrame
        #df = pd.DataFrame(data)

        # Print the output.
        #print(df)
        #df.to_excel("final_570_bjp_outer.xlsx")

        # read the demo2.xlsx file
        #df=pd.read_excel("nm.xlsx")
        #data = {'Name': ['Tom4', 'Joseph4', 'Krish4', 'John4'], 'Age': [22, 221, 19, 18]}
        print("above done")
        df = pd.DataFrame(data)
        print(df)
        print("Below done")
        # appending the data of df after the data of demo1.xlsx
        with pd.ExcelWriter("final_output.xlsx",mode="a",engine="openpyxl",if_sheet_exists="overlay") as writer:
            df.to_excel(writer, sheet_name="Sheet1",header=None, startrow=writer.sheets["Sheet1"].max_row,index=False)
            print('Done')
        del post[:]
        del comment[:]
        del name[:]
        del lives_city[:]
        del lives_state[:]
        del lives_country[:]
        del from_city[:]
        del from_state[:]
        del from_country[:]
        del cell_no[:]
        del anti_pro[:]
        del sentiment_score[:]
        del profile_url[:]
    except:
        del post[:]
        del comment[:]
        del name[:]
        del lives_city[:]
        del lives_state[:]
        del lives_country[:]
        del from_city[:]
        del from_state[:]
        del from_country[:]
        del cell_no[:]
        del anti_pro[:]
        del sentiment_score[:]
        del profile_url[:]
        pass




