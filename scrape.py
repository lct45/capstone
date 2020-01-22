from bs4 import BeautifulSoup
import requests
import json
import operator

def urlScraperReddit(url):
    response = requests.get(url, timeout=3)
    content = BeautifulSoup(response.content, "html.parser")
    #print(content)
    print("puled content")
    dictionary = {}
    test = content.findAll('p', class_="_1qeIAgB0cPwnLhDF9XSiJM")
    print("here")
    for item in test:
        print(item)
    for texting in test:
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

def urlScraperBlind(url):
    response = requests.get(url, timeout=3)
    content = BeautifulSoup(response.content, "html.parser")
    #print(content)
    dictionary = {}
    test = content.find_all('div', class_="detail")
    for item in test:
        print(type(item))
        temp = item.text
        #print(temp)
        #print(type(temp))
        for words in temp.split():
            print(words)
            if words not in dictionary:
                dictionary[words] = 1
            else:
                dictionary[words]+=1
                #print(char) 

    sorted_x = sorted(dictionary.items(), key=operator.itemgetter(1))
    for k, v in sorted_x:
        print("{}                       {}".format(k, v))


def main():
   #urlScraperReddit('https://www.reddit.com/r/cscareerquestions/comments/edqtrq/i_21f_poc_have_a_really_hard_time_fitting_in_bc/')
   urlScraperBlind('https://www.teamblind.com/post/Micarried-during-critical-deadline-BTtgJgJD')




if __name__ == "__main__":
    main()