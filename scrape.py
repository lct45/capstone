from bs4 import BeautifulSoup
import requests
import json

def urlScraper(url):
    response = requests.get(url, timeout=3)
    content = BeautifulSoup(response.content, "html.parser")
    #print(content)
    print("puled content")
    dictionary = {}
    for texting in content.findAll('p', class_="_1qeIAgB0cPwnLhDF9XSiJM"):
        print("in first loop")
        if texting is None:
            print("LETS DANGING CONTINUE")
            continue
        print(texting).text
        for char in texting:
            print("in second loop")
            if char not in dictionary:
                dictionary[char] = 1
            else:
                dictionary[char]=+1
                print(char)




def main():
   urlScraper('https://www.reddit.com/r/cscareerquestions/comments/edqtrq/i_21f_poc_have_a_really_hard_time_fitting_in_bc/')



if __name__ == "__main__":
    main()