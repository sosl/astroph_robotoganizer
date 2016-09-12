import argparse
import ConfigParser
from os import path

import datetime
import time
import getpass 

import urllib2
import pyPdf 
import io

parser = argparse.ArgumentParser(description="Automate astro-ph tasks")

parser.add_argument("--monday", action='store_true', help="Write Monday email")
parser.add_argument("--remind", action='store_true', help="Write reminder email")
parser.add_argument("--slides", action='store_true', help="Prepare slides")

args = parser.parse_args()

suggestionsURL="http://astronomy.swin.edu.au/~soslowski/astroph/suggestions.php"

# The Monday announcement email:
monday_body = '''Dear All,

This %s in the AR staff room we will have the journal club meeting.

Come participate in a quick overview of recent scientific results across a broad
spectrum of astrophysical research and / or other areas of science.

We don't have any speakers yet for this week so please do sign up with a paper
you have read recently. You don't have to understand every little detail to
present so it really doesn't take too much time to prepare an overview.

Would you like to contribute but nothing caught your attention recently? Do you
need some inspiration? Have a look at a list of suggested papers and news:
%s

Some extra details on the usage of this website as well as a refresher about
the journal club's format is available here:
%s

How to submit a paper?

Please post papers for discussion on the journal club wiki:
%s
login: %s
password: %s

Cheers,
%s on behalf of the astro-ph coffee organizers'''

reminder_body = '''Dear All,

Just a friendly reminder about the astro-ph coffee in about %d minutes in the AR
staff room.

If you wish you can grab a discounted coffee from Haddons.

We have %d speakers lined up for today:
%s

We hope to see many of you there,

%s on behalf of the astro-ph coffee organizers
'''

Config = ConfigParser.ConfigParser()
Config.read(path.expanduser("~/.astroph_robotoganizerrc"))
sender = Config.get("User", "Name")
wiki_paper_list_URL = (Config.get("Wiki", "BaseURL") + 
    Config.get("Wiki", "PaperListExt"))
wiki_login_URL = (Config.get("Wiki", "BaseURL") + 
    Config.get("Wiki", "LoginAndReturnExt"))
wiki_format_URL = (Config.get("Wiki", "BaseURL") + 
    Config.get("Wiki", "FormatExt"))

wiki_username = raw_input("Please provide wiki username: ")
wiki_passwd = getpass.getpass()

def suffix(d):
        return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

def fetch_astroph_papers( friday, login_url, astroph_db_url, name, passwd ):
    import urllib
    import cookielib
    # import BeautifulSoup, both version 3 and 4 should be fine
    try:
        import BeautifulSoup
        #print "Using BeautifulSoup version 3"
    except ImportError:
        try:
            import bs4 as BeautifulSoup
            #print "Using BeautifulSoup version 4"
        except ImportError:
            print "Please install BeautifulSoup version 3 or 4 before continuing"
            exit(1)
    data = { "wpName" : name, "wpPassword" : passwd }
    enc_data = urllib.urlencode(data)

    cookies = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies))
    urllib2.install_opener(opener)

    req = urllib2.Request(login_url, enc_data)
    handle = urllib2.urlopen(req)

    req = urllib2.Request(astroph_db_url)
    handle = urllib2.urlopen(req)

    html = handle.read()
    soup = BeautifulSoup.BeautifulSoup(html, 'lxml')

    # potential papers:
    h1s = soup.find_all(name="h1")
    # we use this string to identify a day entry:
    match_key_str = "Papers to discuss on " 
    # generate a date string that will be used to find out which astro-ph db entries
    # are for the upcoming Friday
    friday_str = friday.strftime("%d %B").lstrip("0")

    day_found = False
    papers = []
    for h1 in h1s:
        day_found = match_key_str + friday_str in h1.get_text()
        if day_found:
            paper = h1.findNextSibling().findNextSibling()
            while paper.name == "h2":
                # this is very highly reliant on the specific format we use so not at
                # all portable:
                paper_title = paper.get_text().lstrip("[edit] ")
                paper_a_tag = paper.find_next("a", attrs={"class", "external free"})
                paper_url = paper_a_tag.attrs['href']
                paper_pdf = paper_url.replace("abs","pdf") +".pdf"
                paper_poster_tag = paper_a_tag.findNext()
                tmp = paper_poster_tag.get_text().split()
                paper_poster = tmp[len(tmp)-1]
                papers.append([paper_title, paper_url, paper_pdf, paper_poster])
                paper = paper_poster_tag.findNextSibling().findNextSibling()
            break
    return papers

# Determine the next Friday
#today = datetime.date.today()
today = datetime.datetime.now()
friday = today + datetime.timedelta( (4-today.weekday()) % 7 )
friday_exact = datetime.datetime(friday.year, friday.month, friday.day,
        11, 30, 0)
# Human friendly Friday date
friday_str = custom_strftime("%A, {S} of %B at 11:30 AM", friday_exact)

# print Monday email to stdout
if args.monday:
    print monday_body % (friday_str, suggestionsURL, wiki_format_URL, wiki_paper_list_URL,
            wiki_username, wiki_passwd, sender )

# Fetch a list of contributions from the wiki
if args.remind or args.slides:
    papers = fetch_astroph_papers(friday_exact, wiki_login_URL,
        wiki_paper_list_URL, wiki_username, wiki_passwd )


# TODO Replace with a text that lists the papers and contributors
paper_list = "TODO LIST OF PAPERS GOES HERE"
if args.remind:
    # get time difference via unix timestamps
    time_diff_minutes = (time.mktime(friday_exact.timetuple()) -
            time.mktime(today.timetuple())) / 60.
    # round to 5 minutes:
    time_diff_minutes = int(5 * round ( time_diff_minutes/5 ))
    print reminder_body % ( time_diff_minutes, len(papers), paper_list, sender)

# Fetch and merge papers into a single pdf:
if args.slides:
    if len(papers) > 0 :
        output = pyPdf.PdfFileWriter()
        for paper in papers:
            url = paper[2]
            if "arxiv.org" in url:
                paper_handle = urllib2.urlopen(url)
                paper_pdf = io.BytesIO(paper_handle.read())
                input_pdf = pyPdf.PdfFileReader(paper_pdf)
                for i in range(0,input_pdf.getNumPages()):
                    output.addPage(input_pdf.getPage(i))
                output.addBlankPage()
            else:
                print paper[1]

        output_fp = open(friday.strftime("astroph_%d_%B.pdf"), "w")
        output.write(output_fp)
        output_fp.close()
    else:
        print "No papers have been posted yet, not generating slides. Prompt people to sign up!"
