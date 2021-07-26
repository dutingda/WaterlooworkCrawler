from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions as se
from bs4 import BeautifulSoup
from selenium.webdriver.common.action_chains import ActionChains
import mysql.connector
import time

browser = webdriver.Chrome()
wait = WebDriverWait(browser, 10)
db = mysql.connector.connect(host='', user='', password='', database='') #fill database info
sql = db.cursor()
actions = ActionChains(browser)


def click(xpath):
    e = wait.until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    e.click()


def typ(xpath, word):
    e = wait.until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )
    e.send_keys(word)


def enter():
    try:
        browser.get('https://waterlooworks.uwaterloo.ca')
        click("/html/body/div[3]/div/div/div[5]/div/div/a[1]")

        typ('//*[@id="username"]', "") #fill account info
        typ('//*[@id="password"]', "")

        click('//*[@id="cas-submit"]/input')
        click('//*[@id="closeNav"]/div/ul/div/ul/li[2]/a')
        click('//*[@id="closeNav"]/div/ul/div/ul/li[2]/div/ul/li[1]/a')
        click('//*[@id="quickSearchCountsContainer"]/table/tbody/tr[1]/td[2]/a')
    except se.TimeoutException as e:
        return 'Timeout, {}'.format(e.__cause__)


def create_db():
    insert = "CREATE TABLE `Store`.`waterlooworkss` (`id` INT NOT NULL,`title` VARCHAR(100)" \
             " NULL,`company` VARCHAR(70) NULL,`city` VARCHAR(45) NULL,`country` VARCHAR(45) NULL,`open` INT NULL," \
             "`summary` TEXT NULL,`responsibility` TEXT NULL,`required` TEXT NULL,`transhousing`" \
             " TEXT NULL,`benefit` TEXT NULL,`duration` VARCHAR(45) NULL,`special` TEXT NULL,`document`" \
             " VARCHAR(145) NULL,`additional` TEXT NULL,`expire` DATE NULL,PRIMARY KEY (`id`),UNIQUE INDEX `id_UNIQUE` " \
             "(`id` ASC) VISIBLE);"
    sql.execute(insert)
    db.commit()


def to_database(job):
    insert = "INSERT INTO waterlooworks (id,title,company,city,country,open,summary,responsibility," \
             "required,transhousing,benefit,duration,special,document,additional,expire) " \
             "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    try:
        sql.execute(insert, (job.get("id"),job.get("ti"),job.get("com"),job.get("city"),job.get("con"),job.get("open"),
                         job.get("sum"),job.get("resp"),job.get("req"),job.get("th"),job.get("ben"),
                         job.get("dur"),job.get("spe"),job.get("doc"),job.get("add"),"2019-01-29"))
        db.commit()
        print("{} done".format(job.get("id")))
    except mysql.connector.errors.DataError as e:
        print("{0}: {1}".format(job.get("id"),e.msg))
        return
    except mysql.connector.errors.IntegrityError as e:
        if e.msg.find("Duplicate")>-1:
            command = "UPDATE `waterlooworks` SET `expire` = '2019-01-29' WHERE (`id` = '{}');".format(job.get("id"))
            sql.execute(command)
            db.commit()
            print("Updated {}".format(job.get("id")))
        else:
            print("{0}: {1}".format(job.get("id"), e.msg))
        return


def one_job(num):
    time.sleep(0.4)
    company = browser.find_element_by_xpath('//*[@id="{}"]/td[5]/span'.format(num)).text
    try:
        click('//*[@id="{0}"]/td[4]/*/a | //*[@id="{0}"]/td[4]/*/*/a'.format(num))
    except se.TimeoutException:
        print("{} error".format(num))
        return
    except se.WebDriverException:
        print("{} not clickable".format(num))
        return

    browser.switch_to.window(browser.window_handles[1])
    jid = num[7:]

    soup = BeautifulSoup(browser.page_source, features="html.parser").find(class_="span8").find_all(class_="panel panel-default")
    job_info = soup[0].find_all("tr")
    app_info = soup[1].find_all("tr")

    job = {"id": jid, "com": company.replace("\n", "").replace("\t", "")}
    for j in job_info:
        j = j.find_all("td")
        if len(j) < 2:
            continue
        title = j[0].text.replace("\n", "").replace("\t", "")
        content = j[1].text.replace("\n", "").replace("\t", "")
        if title == "Job Title:":
            job["ti"] = content
        elif title == "Job - City:":
            job["city"] = content
        elif title == "Job - Country:":
            job["con"] = content
        elif title == "Number of Job Openings:":
            job["open"] = content
        elif title == "Job Summary:":
            job["sum"] = content
        elif title == "Job Responsibilities:":
            job["resp"] = content
        elif title == "Required Skills:":
            job["req"] = content
        elif title == "Transportation and Housing:":
            job["th"] = content
        elif title == "Compensation and Benefits Information:":
            job["ben"] = content
        elif title == "Work Term Duration:":
            job["dur"] = content
        elif title == "Special Job Requirements:":
            job["spe"] = content
    for i in app_info:
        i = i.find_all("td")
        if len(i) < 2:
            continue
        title = i[0].text.replace("\n", "").replace("\t", "")
        content = i[1].text.replace("\n", "").replace("\t", "")
        if title == "Application Documents Required:":
            job["doc"] = content
        elif title == "Additional Application Information:":
            job["add"] = content
    to_database(job)
    browser.close()
    browser.switch_to.window(browser.window_handles[0])


def one_list():
    soup = BeautifulSoup(browser.page_source, features="html.parser")
    ids = soup.find(id="postingsTableDiv").find("tbody").find_all("tr")
    for i, jid in enumerate(ids):
        ids[i] = jid["id"]
        one_job(ids[i])


def fetch():
    soup = BeautifulSoup(browser.page_source, features="html.parser")
    #ids = soup.find(id="postingsTableDiv").find("tbody").find_all("tr")
    next_page_button = len(soup.find(id="postingsTablePlaceholder").find(class_="orbis-posting-actions").find(class_="pagination pagination").find_all("li"))-1

    '''
    time.sleep(2)
    click('//*[@id="postingsTablePlaceholder"]/div[1]/div/ul/li[5]/a')
    browser.execute_script("window.scrollTo(0, 400)")
    time.sleep(5)
    click('//*[@id="posting99823"]/td[4]/span[2]/a')
    '''
    click('//*[@id="postingsTablePlaceholder"]/div[1]/div/ul/li[9]/a')
    for i in range(1):
        time.sleep(8)
        one_list()
        time.sleep(8)
        try:
            print("{}th page done".format(i))
            click('//*[@id="postingsTablePlaceholder"]/div[4]/div/ul/li[{}]/a'.format(next_page_button))
            browser.execute_script("window.scrollTo(0, 0)")
        except se.TimeoutException:
            print(browser.page_source)


def apply(lis):
    typ('//*[@id="widget1Keyword"]', lis[0])
    click('//*[@id="filterForm"]/div/button[1]')
    try:
        click('//*[@id="posting{}"]/td[1]/a[1]'.format(lis[0]))
        click('//*[@id="posting{}"]/td[1]/a[2]'.format(lis[0]))
        click('//*[@id="applyToPostingForm"]/div/div[2]/div[1]/div[1]/label')
        click('//*[@id="applyToPostingForm"]/div/div[2]/input')  # complete application with default package
        click('//*[@id="mainContentDiv"]/div[2]/div/div/div[2]/div[2]/div/a[2]')  # back to search
    except se.TimeoutException:
        print("{} is not available to apply".format(lis[0]))

    for i in lis[1:]:

        typ('//*[@id="widget1Keyword"]', i)
        click('//*[@id="filterForm"]/div/button[1]')
        try:
            click('//*[@id="mainContentDiv"]/div[2]/div/div/div/div[2]/div/div/div/div/div[2]/div/a[2]')  # clear search
            click('//*[@id="posting{}"]/td[1]/a[1]'.format(i))
            click('//*[@id="posting{}"]/td[1]/a[2]'.format(i))
            click('//*[@id="applyToPostingForm"]/div/div[2]/div[1]/div[1]/label')
            click('//*[@id="applyToPostingForm"]/div/div[2]/input')#complete application with default package
            click('//*[@id="mainContentDiv"]/div[2]/div/div/div[2]/div[2]/div/a[2]')#back to search
        except se.TimeoutException:
            continue


def main():
    enter()
    #fetch()
    apply([])#fill in list of job ids


if __name__ == '__main__':
    main()