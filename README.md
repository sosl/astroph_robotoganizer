# astroph_robotoganizer

This is a simple script to make some of the tasks related to organizing astroph-coffee / journal club easier. The functionality includes:

* Writing an announcement email
* Writing a reminder email
* Gathering the pdfs for arxiv papers that people will discuss and merge them into a single pdf

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisities

This script relies on the following packges:

* os
* argparse
* ConfigParser
* time
* datetime
* getpass
* cookielib
* urllib
* urllib2
* pyPdf
* io
* BeautifulSoup (both 3 and 4 will work)

### Installing

Simply download the script and create a configuration file `~/.astroph_robotoganizerrc` in your home directory. The repo includes an example of such a file

## Authors

* **Stefan Oslowski**


## License

This project is licensed under the GNU GPL version 3 license - see the [LICENSE.md](LICENSE.md) file for details
