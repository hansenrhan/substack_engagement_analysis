import requests
import pandas as pd
import json
import time
from bs4 import BeautifulSoup
from tqdm import tqdm
import re
import nltk
from nltk.corpus import words, stopwords
import nltk.data
import textstat
from textblob import TextBlob
import sqlite3

nltk.download('words')
nltk.download('stopwords')

def get_posts_for_blog(blog_url):
    # returns a dataframe of blog posts and metadata for them
    count = 12

    continue_scrape = True

    # collect data
    result_data = []

    while continue_scrape:
        r = requests.get(blog_url + "/api/v1/archive?sort=new&search=&offset={count}&limit=12".format(count = count))

        post_data = json.loads(r.text)
        for post in post_data:
            result_data.append({
                "title": post['title'],
                "audience": post["audience"],
                "canonical_url": post["canonical_url"],
                "description": post["description"],
                "truncated_body_text": post["truncated_body_text"],
                "wordcount": post["wordcount"],
                "reaction_count": post["reaction_count"],
                "comment_count": post["comment_count"],
                "post_date": post["post_date"]
            })

        # TODO - I want to add the author, and how long the author has been posting

        
        if len(post_data) < 12:
            continue_scrape = False
        else:
            count = count + 12
        
        time.sleep(5)
    
    return pd.DataFrame(result_data)
        
def remove_special_characters(input_string):
    # Define a pattern to match special characters
    pattern = r'[^a-zA-Z0-9\s]'  # This pattern will keep alphanumeric characters and spaces
    
    # Use the re.sub function to replace matched patterns with an empty string
    cleaned_string = re.sub(pattern, '', input_string)
    
    return cleaned_string

def is_real_word(word):
    word = word.lower()  # Convert to lowercase for case-insensitive comparison
    return word in words.words()

def count_question_sentences(text):
    # Initialize the sentence tokenizer
    sentence_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    
    # Tokenize the text into sentences
    sentences = sentence_tokenizer.tokenize(text)
    
    # Initialize a counter for question sentences
    question_count = 0
    
    # Define a regex pattern to match question sentences
    question_pattern = r'^[A-Z][^.?!]*\?$'
    
    # Iterate through the sentences and check if they are questions
    for sentence in sentences:
        if re.match(question_pattern, sentence):
            question_count += 1
            
    return question_count

def get_readability_level(text):
    # Calculate the Flesch-Kincaid Grade Level
    fk_grade_level = textstat.flesch_kincaid_grade(text)
    
    # Calculate the Gunning Fog Index
    gunning_fog_index = textstat.gunning_fog(text)
    
    return fk_grade_level, gunning_fog_index

def extract_value_by_key(dictionary, target_key):
    # Check if the target_key is in the current dictionary
    if target_key in dictionary:
        return dictionary[target_key]
    
    # If the key is not found, recursively search in nested dictionaries
    for key, value in dictionary.items():
        if isinstance(value, dict):
            result = extract_value_by_key(value, target_key)
            if result is not None:
                return result
    
    # If the key is not found anywhere in the dictionary, return None
    return None

def extract_tokens_from_text(text):
    text = text.split(" ")

    # clean values
    text = [remove_special_characters(x.replace("[", "").replace("]", "").replace(",", " ").replace("\n", " ").replace("  ", " ").replace("nnn", " ")) for x in text]

    # standardize, make them all lowercase, remove urls
    text = [x.lower() for x in text]

    # remove stop words and words that aren't words
    stop_words = set(stopwords.words('english'))
    english_words = set(words.words())

    text = [word for word in text if word not in stop_words]
    tokens = [word for word in text if word in english_words]
    return tokens

def get_element_counts_from_html(soup_object):
    # Initialize a dictionary to store element counts
    element_counts = {}

    # extract the text for every div on the page
    count_elements(soup_object)
    
    # count the number of elements
    return element_counts

def get_article_html(soup_object):
    # Assuming you have the HTML content of the page loaded into BeautifulSoup as 'soup'
    # Find the script element containing the JSON data
    script_elements = soup_object.find_all("script")

    for script_element in script_elements:
        if "subscribers" in script_element.text:
            break

    input_string = script_element.text
    
    # Find the JSON data within the string
    start_index = input_string.find('JSON.parse(') + len('JSON.parse(')
    end_index = input_string.rfind(');', start_index)

    # Extract the JSON data
    json_data = input_string[start_index:end_index].strip()

    # Parse the JSON data into a dictionary
    parsed_dict = json.loads(json_data)
    

    formatted_dict = json.loads(parsed_dict)

    target_key = "body_html"
    article_html = extract_value_by_key(formatted_dict, target_key)
    return article_html

def estimate_reading_time(text, words_per_minute=200):
    words = text.split()
    word_count = len(words)
    
    if word_count <= 0:
        return 0
    
    reading_time_minutes = word_count / words_per_minute
    return reading_time_minutes


def get_post_metadata(post_dataframe):
    # add on metadata for each post
    tokens_results = []
    raw_text_results = []
    p_elem_counts = []
    a_elem_counts = []
    img_elem_counts = []
    ul_elem_counts = []
    li_elem_counts = []
    br_elem_counts = []
    video_elem_counts = []
    polarity_results = []
    objectivity_results = []
    num_questions_results = []
    fk_grade_level_results = []
    gunning_fog_index_results = []
    reading_time_results = []
    
    for post_url in tqdm(post_dataframe['canonical_url']):

        # reset all values that are being appended from the last round in case of errors
        text = None
        soup = None
        polarity = None
        objectivity = None
        fk_grade_level = None
        gunning_fog_index = None

        # get article
        r = requests.get(post_url)
        soup = BeautifulSoup(r.text)

        # Initialize a dictionary to store element counts

        # get the article body html
        article_html = get_article_html(soup)

        # get the counts of the elements
        soup = BeautifulSoup(article_html)

        # Count the number of <p> elements
        p_elem_counts.append(len(soup.find_all('p')))

        # Count the number of <img> elements
        img_elem_counts.append(len(soup.find_all('img')))

        # Count the number of <a> elements
        a_elem_counts.append(len(soup.find_all('a')))

        # count the number of <ul> elements
        ul_elem_counts.append(len(soup.find_all('ul')))

        # count the number of <li> elements
        li_elem_counts.append(len(soup.find_all('li')))

        # count the number of <video> elements
        video_elem_counts.append(len(soup.find_all('video')))

        # count the number of <br> elements
        br_elem_counts.append(len(soup.find_all('br')))
        
        # convert html to raw text 
        text = re.sub(r'\xa0', ' ', soup.get_text())
        try:
            raw_text_results.append(text)
        except:
            raw_text_results.append(None)

        # extract tokens from the text
        tokens_results.append(extract_tokens_from_text(text))

        # get polarity and objectivity
        blob = TextBlob(text)
        polarity, objectivity = blob.sentiment
        polarity_results.append(polarity)
        objectivity_results.append(objectivity)

        # count the number of questions
        num_questions_results.append(count_question_sentences(text))

        # get readability metrics
        fk_grade_level, gunning_fog_index = get_readability_level(text)
        fk_grade_level_results.append(fk_grade_level)
        gunning_fog_index_results.append(gunning_fog_index)

        # get reading time estimates
        reading_time_results.append(estimate_reading_time(text))

  
    post_dataframe["tokens"] = tokens_results
    #post_dataframe["raw_text"] = raw_text_results
    post_dataframe["polarity"] = polarity_results
    post_dataframe["objectivity"] = objectivity_results
    post_dataframe["number_of_questions"] = num_questions_results
    post_dataframe["fk_grade_level"] = fk_grade_level_results
    post_dataframe["gunning_fog_index"] = gunning_fog_index_results
    post_dataframe["reading_time"] = reading_time_results
    post_dataframe["p_elem_counts"] = p_elem_counts
    post_dataframe["a_elem_counts"] = a_elem_counts
    post_dataframe["img_elem_counts"] = img_elem_counts
    post_dataframe["ul_elem_counts"] = ul_elem_counts
    post_dataframe["li_elem_counts"] = li_elem_counts
    post_dataframe["video_elem_counts"] = video_elem_counts
    post_dataframe["br_elem_counts"] = br_elem_counts

    return post_dataframe

def get_post_metadata_from_url(post_url):

    # get article
    r = requests.get(post_url)
    soup = BeautifulSoup(r.text)

    # Initialize a dictionary to store element counts

    # get the article body html
    article_html = get_article_html(soup)

    # get the counts of the elements
    soup = BeautifulSoup(article_html)

    # Count the number of <p> elements
    p_elem_counts = len(soup.find_all('p'))

    # Count the number of <img> elements
    img_elem_counts = len(soup.find_all('img'))

    # Count the number of <a> elements
    a_elem_counts = len(soup.find_all('a'))

    # count the number of <ul> elements
    ul_elem_counts = len(soup.find_all('ul'))

    # count the number of <li> elements
    li_elem_counts = len(soup.find_all('li'))

    # count the number of <video> elements
    video_elem_counts = len(soup.find_all('video'))

    # count the number of <br> elements
    br_elem_counts = len(soup.find_all('br'))
    
    # convert html to raw text 
    text = re.sub(r'\xa0', ' ', soup.get_text())
    try:
        raw_text_results = text
    except:
        raw_text_results = None

    # extract tokens from the text
    try:
        tokens_results = extract_tokens_from_text(text)
    except:
        tokens_results = None

    # get polarity and objectivity
    try:
        blob = TextBlob(text)
        polarity, objectivity = blob.sentiment
        polarity_results = polarity
        objectivity_results = objectivity
    except:
        polarity_results = None
        objectivity_results = None

    # count the number of questions
    try:
        num_questions_results = count_question_sentences(text)
    except:
        num_questions_results = None

    # get readability metrics
    try:
        fk_grade_level, gunning_fog_index = get_readability_level(text)
        fk_grade_level_results = fk_grade_level
        gunning_fog_index_results = gunning_fog_index
    except:
        fk_grade_level_results = None
        gunning_fog_index_results = None

    # get reading time estimates
    try:
        reading_time_results = estimate_reading_time(text)
    except:
        reading_time_results = None

    result_dict = {
        "p_elem_counts": p_elem_counts,
        "img_elem_counts": img_elem_counts,
        "a_elem_counts": a_elem_counts,
        "ul_elem_counts": ul_elem_counts,
        "li_elem_counts": li_elem_counts,
        "video_elem_counts": video_elem_counts,
        "br_elem_counts": br_elem_counts,
        "raw_text_results": raw_text_results,
        "tokens_results": tokens_results,
        "polarity_results": polarity_results,
        "objectivity_results": objectivity_results,
        "num_questions_results": num_questions_results,
        "fk_grade_level_results": fk_grade_level_results,
        "gunning_fog_index_results": gunning_fog_index_results,
        "reading_time_results": reading_time_results
    }

    return result_dict

