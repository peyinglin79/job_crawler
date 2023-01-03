# 1111_bank
from bs4 import BeautifulSoup as bs
import requests
import pymysql
import re

urls=[]
soup1=[]
jobid=[]
newjobid=[]
jobwebs=[]
result=[]
titles=[]
titles2=[]
final=[]

# headers
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}

for i in range(1,61):
    url = f'https://www.1111.com.tw/search/job?ks=python&page={i}&tt=1'
    urls.append(url)

for i in urls:
    response = requests.get(i, headers=headers)
    soup = bs(response.text, 'html.parser')
    soup1.append(soup)

# 找出屬性data-eno(jobid)
for i in soup1:
    for n in range(len(i.find_all('div', class_='item__job job_item'))):
        job_id = i.find_all('div', class_='item__job job_item')[n].attrs['data-eno'] 
        jobid.append(job_id)

# 篩選掉重複的jobid
for ids in jobid:
    if ids not in newjobid:
        newjobid.append(ids)

# 每個職缺的網址
for i in newjobid:
    job_web = f'https://www.1111.com.tw/job/{i}/'
    r = requests.get(job_web, headers=headers)
    data = bs(r.text, 'html.parser')
    result.append(data)


# find所需的資料
for i in result:
    try:
        newid = i.find('link').attrs['href'].split('/')[-2]
        jobname = i.find('h1',class_='title_4').text.replace(' ','').replace('*','')
        company = i.select_one('div.ui_card_company span').text
        location = i.find('div',class_='ui_items job_location').text.replace(' ','').replace('\n','').replace('\r','')
        salary = i.find('div', class_='ui_items job_salary').text.replace(' ','').replace('\n','').replace('\r','')
        if '面議' in salary:
            salaryannual = 480000
        elif '年薪' in salary:
            yearly = r'\d+'
            salary = re.findall(yearly, salary)
            salaryannual = eval(salary[0])*10000
        elif ',' in salary:
            monthly = r'\d+'
            salary = re.findall(monthly, salary)
            salary = eval(''.join(salary))
            salaryannual = salary*12
        elif '月薪' and '萬' in salary:
            monthly = r'\d+\.?\d*'
            salary = re.findall(monthly, salary)
            salary = eval(salary[0])*10000
            salaryannual = salary*12
        elif '月薪' in salary:
            monthly = r'\d+\.?\d*'
            salary = re.findall(monthly, salary)
            salary = eval(salary[0])
            salaryannual = salary*12
        update = i.find('small', class_='text-muted job_item_date body_4').text.split(' ')[1]
        edu = i.find('div', class_='ui_items job_education').text.replace(' ','').replace('\n','').replace('\r','')        
        # condition
        condition = i.find_all('div', class_='content_items job_skill')
        # dep(固定在第三項)
        for i in condition:
            dep = i.find_all('span', class_='job_info_content')[2].text
            dep = dep.replace(' ','').replace('\n','').split('\r')    
            
            for i in dep:
                if '' in dep:
                    dep.remove('')
        dep = ','.join(dep)    
        # skill
        for i in condition:
            # 判斷要求條件中有無「電腦專長」
            title1 = i.find_all('span', class_='job_info_title')    
            for t in title1:
                t = t.text
                titles.append(t) 
            try:
                if '電腦專長：' in titles:
                    c_index = titles.index('電腦專長：')
                    #
                    for i in condition:
                        skill = i.find_all('span', class_='job_info_content')[c_index].text
                        skill = skill.replace(' ','').replace('\n','').split('\r')
                            
                        while '' in skill:
                            skill.remove('')
                    skill = ','.join(skill)
                else:
                    skill=''    
            except:
                skill=''    
        # 附加條件
        for i in condition:
            # 判斷要求條件中有無「附加條件」
            title2 = i.find_all('div', class_='job_info_title')
            for t in title2:
                t = t.text
                titles2.append(t)
            try:
                if '附加條件：' in titles2:
                    u_i_g = i.find_all('div', class_='ui_items_group')
                    a_index = len(u_i_g)-1
                    #    
                    attached = i.find_all('div', class_='ui_items_group')[a_index].text
                    attached = attached.replace(' ','').replace('\n','').replace('\r','').replace('\t','')        
                else:
                    attached = ''    
            except:
                attached = ''
        
        titles.clear()
        titles2.clear()
            
        # 整合所有欄位
        job = {'id':newid,
                'jobname':jobname,
                'company':company,
                'city':location[0:3],
                'dist':location[3:6],
                'salary':salaryannual,
                'update':update,
                'edu':edu,
                'dep':dep,
                'skill':skill,
                'attached':attached}       
                    
        final.append(job)
        
    except:
        print(newid) #toplink找不到頁面
        continue


###
# 匯入至資料庫
con = pymysql.connect(host= "",
                          port= ,
                          user= "",
                          password= "",
                          database = "")

if con.open:
    cur = con.cursor()
    print('Connected to MySQL successfully.\n')
 
    sql='''CREATE TABLE IF NOT EXISTS `job_1111`(
                `id` int primary key,
                `jobname` varchar(100),
                `company` varchar(100),
                `city` varchar(10),
                `dist` varchar(10),
                `salary` int,
                `education` varchar(20),
                `department` varchar(100),
                `skill` varchar(500),
                `attached` varchar(10000),
                `lastupdate` date,
                `website` varchar(10));'''        
    cur.execute(sql)

    try:
        for i in range(len(final)):
            sql='''
                INSERT INTO `career`.`job_1111` (`id`,`jobname`,`company`,`city`,`dist`,`salary`,`education`,`department`,`skill`,`attached`,`lastupdate`,`website`)
                VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','1111') on duplicate key update jobname=values(jobname),company=values(company),city=values(city),dist=values(dist),salary=values(salary),education=values(education),department=values(department),skill=values(skill),attached=values(attached),lastupdate=values(lastupdate),website=values(website);
                '''.format(final[i]['id'], final[i]['jobname'], final[i]['company'], final[i]['city'], final[i]['dist'], final[i]['salary'], final[i]['edu'], final[i]['dep'], final[i]['skill'], final[i]['attached'],final[i]['update'])
            cur.execute(sql)    
        print('Values inserted successfully.\n')
                
    except Exception as m:
        print('Something went wrong:', m, '\n')
        print(final[i]['id'], final[i]['jobname'],'\n')

else:
    print('Connection failed.')

con.commit()
cur.close()
con.close()
print('Quit MySQL')