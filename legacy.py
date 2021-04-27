# 모듈
from bs4 import BeautifulSoup
from selenium import webdriver
import re
import pymysql
from time import sleep
from collections import OrderedDict
import random

from set_info import *

# 웹드라이버로 ntis 접속
driver = webdriver.Chrome(r'C:\Users\sweet\Downloads\chromedriver_win32(1)\chromedriver.exe')
driver.get("https://www.ntis.go.kr/ThMain.do")

# 팝업창 닫기
#driver.switch_to.window(driver.window_handles[-1])
#driver.find_element_by_xpath("""/html/body/div/div/div[2]/div[2]/label""").click()
#driver.find_element_by_xpath("""//*[@id="btnClose2"]""").click()
#driver.switch_to.window(driver.window_handles[0])


element = driver.find_element_by_xpath("/html/body/div[4]/div/div[2]/div[1]/button")
driver.execute_script("arguments[0].click();", element)
# 로그인 팝업 창으로 변경
driver.switch_to.window(driver.window_handles[-1])

# 아이디 입력
elem_login = driver.find_element_by_xpath("""/html/body/div/form/label[2]/input""")
elem_login.clear()
elem_login.send_keys(['NTIS']['id'])

# 비번 입력
elem_login = driver.find_element_by_xpath("""/html/body/div/form/label[4]/input""")
elem_login.clear()
elem_login.send_keys(['NTIS']['pw'])

# 로그인 버튼 누름
xpath = """/html/body/div/form/input"""
driver.find_element_by_xpath(xpath).click()

# 메인 창으로 변경
driver.switch_to.window(driver.window_handles[0])

def search_url(word, num):
    # 검색 페이지 url
    search_url_word = word
    search_url_base = "https://www.ntis.go.kr/ThSearchProjectList.do?sort=RANK%2FDESC&ntisYn=&searchWord="

    # 페이지 번호 url
    search_url_sub = "&searchType=&oldSearchWord="
    search_url_sub2 = "&resultSearch=&pageNumber=%d" % (num)
    search_url_sub3 = "&ssoKnfSlct=0&ascDesc=ASC&useYn=N&oldQuery="

    # 100개씩 보기 
    search_url_sub4 = "&oldAddQuery=I03%3D1%2FNOTSAME&pageYn=Y&downloadTarget=rindust&startRow=&endRow=&rqstPurpCd=&infoPrctuseDes=&sort=RANK%2FDESC&pageSize=100"

    url = search_url_base + search_url_word + search_url_sub + search_url_word + search_url_sub2 + search_url_sub3 + search_url_word + search_url_sub4
    
    return url

keyword_seq=[("가명화",1),("익명화", 2)]
# mysql 연결
conn = pymysql.connect(host = ['DB']['host'], user = ['DB']['user'], password =  ['DB']['password'], db = ['DB']['db'], charset = ['DB']['utf8'])
bus_key=0
rf_num=0
commercialization_num=0

fee_curs=conn.cursor()
pjt_curs = conn.cursor()
rf_curs=conn.cursor()
bus_curs = conn.cursor()
com_curs=conn.cursor()
pjtid_search_curs=conn.cursor()


# 페이지 번호 url
for key in keyword_seq:
    num = 1
    url=search_url(key[0], num)
    # 검색 결과 목록 창 열기
    driver.get(url)
    # 딜레이
    sleep(3) 
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    # 페이지 수 구하기
    count_soup = soup.select('#content > div.list_box > div.related_word')[0].text
    retext = re.sub('[\n\t\xa0]', '', count_soup)
    splittext = retext.split('/')[1]
    repeatStr=re.findall('[0-9,]+건', splittext)[0]
    numStr="" 
    for page in range(len(repeatStr)):
        if page!=len(repeatStr)-1 and repeatStr[page]!=',':
            numStr+=repeatStr[page]
    repeatNum = int(numStr)//100 +1
    
    print(repeatNum)
    
    #과제 번호 수집
    pjt_id_list = []
    for rep in range(repeatNum):
        driver.get(url)
        #delay 시간 10~30초로 랜덤 지정
        delay = random.randrange(2,4)
        sleep(delay)
        try :
            # html 소스코드 저장
            search_html=driver.page_source
        except :
            # 페이지 새로고침 
            driver.refresh()
            search_html = driver.page_source

        search_soup = BeautifulSoup(search_html, 'html.parser')
        # selector를 이용
        pjt_soup = search_soup.select('.mdata')

        for soup in pjt_soup :
            idNum=re.sub('[()]\n\t', '', soup.select('span')[0].text)
            id_list=re.findall('[0-9]{10}', idNum)
            if not id_list:
                pass
            else:
                pjt_id_list.append(id_list[0])
                
        num = num+1
        url=search_url(key[0], num)
        
    pj_url_base = "https://www.ntis.go.kr/project/pjtInfo.do?pjtId="
    keywords=key[1]
    print(key[1])

    for popup in pjt_id_list:
        #DB 확인
        print(popup)

        pjt_check_sql="SELECT * FROM ntis_KM.project where pjt_id='%s'"%popup
        pjtid_search_curs.execute(pjt_check_sql)
        conn.commit()
        pjt_result=pjtid_search_curs.fetchall()
        pjtid_search_curs.close()
        pjtid_search_curs=conn.cursor()
        
        if pjt_result!=():
            continue

        delay = random.randrange(2,3)
        sleep(delay)
        
        try:
            pjt_url = pj_url_base + popup
            driver.get(pjt_url)
            delay = random.randrange(2, 4)
            sleep(delay)
            pjt_html = driver.page_source
            pjt_soup = BeautifulSoup(pjt_html, 'html.parser')

            # 사업 테이블 정보 
            pjt_main3 = pjt_soup.select('#content > div.po_rel > dl.result_off > dd')[0].text
            pjt_main3_info=pjt_main3.split('/')

            bus_year=re.findall('[0-9]{4}', pjt_main3)[0]
            bus_section = re.sub('[\t\n]', '',pjt_main3_info[2]).strip()
            bus_agency = re.sub('[\t\n]', '',pjt_main3_info[1]).strip()
            bus_name=re.sub('[\t|\n]', '',pjt_main3_info[3]).strip()

            # 과제 테이블 정보
            pjt_name_soup = pjt_soup.select('#content > div.po_rel > dl.pjtheader > dd > span.head')
            pjt_name = re.sub('[\t\n]', '', pjt_name_soup[0].text).strip()

            pjt_fee_td=pjt_soup.select('#tbAmt > tbody > tr > td.seltr')[3].text
            pjt_fee=pjt_fee_td.replace('.', '')+'0000'

            pjt_main1 = pjt_soup.select('#divMain > table > tbody')[0]
            pjt_main1_td = pjt_main1.select('tr > td')
            pjt_id = pjt_main1_td[14].text
            pjt_detail_num = pjt_main1_td[15].text
            pjt_detail_name = pjt_main1_td[2].text
            pjt_name_ko = pjt_main1_td[2].text
            pjt_name_en = pjt_main1_td[3].text
            TPA = re.sub('[\t\n]', '', pjt_main1_td[1].text).strip()
            RMSA = pjt_main1_td[4].text
            TMO = pjt_main1_td[5].text

            pjt_progress = re.sub('[\t\n]', '', pjt_main1_td[6].text).strip()
            practical_target = pjt_main1_td[7].text
            RnD_phase = pjt_main1_td[8].text
            RnD_main_agent = pjt_main1_td[9].text
            detailed_pjt_nature = pjt_main1_td[10].text
            RnD_nature = pjt_main1_td[11].text
            tech_life_cycle = pjt_main1_td[12].text
            location = re.sub('[\t\n]', '' , pjt_main1_td[13].text).strip()

            pjt_main2 = pjt_soup.select('.tablecell > table > tbody')[0]
            pjt_main2_per1=pjt_soup.select('#chartdiv1 > div > div > svg > g > text')
            pjt_main2_per2=pjt_soup.select('#chartdiv2 > div > div > svg > g > text')
            pjt_main2_per1_len=len(pjt_main2_per1)
            pjt_main2_per2_len=len(pjt_main2_per2)
            pjt_main2_td = pjt_main2.select('tr > td')

            pj_6T = pjt_main2_td[0].text
            NTRM = pjt_main2_td[1].text

            pjt_main2_text=pjt_soup.select('div.amChartsLegend > svg > g > g > g > text')
            pjt_main2_td = pjt_main2.select('tr > td')
            pjt_CSTS=""
            pjt_applied=""

            for o in range(pjt_main2_per1_len-1):
                pjt_CSTS+=pjt_main2_text[o].text+" ("+pjt_main2_per1[o+1].text+") "
            for k in range(pjt_main2_per2_len-1):
                pjt_applied+=pjt_main2_text[k+pjt_main2_per1_len-1].text+" ("+pjt_main2_per2[k+1].text+") "
            CSTS = re.sub('[\t\n]', '', pjt_CSTS).replace('/', ' | ').strip()
            applied_field = re.sub('[\t\n]', '' ,pjt_applied).strip()

            pjt_summary = pjt_soup.select('#divSummary > div')
            pjt_keyword=pjt_summary[0].select('dd')

            research_objective = re.sub('[\t\n\u3000]', '',pjt_summary[1].text).replace('○', '|').replace('󰋯', '|').replace('◾','|').replace('•', '|').replace('𐩒', '|').replace('□', '|').replace('■','|').replace('◆','|').replace('▲','|').replace('●', '|').replace('▣','|').replace('▷', '|').replace('▶', '|').replace('￭','|').replace('◯', '|').replace('⚪','|').replace('�','|').strip()
            research_content = re.sub('[\t\n]','',pjt_summary[2].text).replace('○', '|').replace('󰋯', '|').replace('◾','|').replace('•', '|').replace('𐩒', '|').replace('□', '|').replace('■','|').replace('◆','|').replace('▲','|').replace('●', '|').replace('▣','|').replace('▷', '|').replace('▶', '|').replace('￭','|').replace('◯', '|').replace('⚪','|').replace('�','|').strip()
            expect_effect = re.sub('[\t\n]', '', pjt_summary[3].text).replace('○', '|').replace('󰋯', '|').replace('◾','|').replace('•', '|').replace('𐩒', '|').replace('□', '|').replace('■','|').replace('◆','|').replace('▲','|').replace('●','|').replace('▣', '|').replace('▷', '|').replace('▶', '|').replace('￭','|').replace('◯', '|').replace('⚪','|').replace('�','|').strip()
            keywords_ko = re.sub('[\t\n]', '', pjt_keyword[0].text).replace('○', '|').replace('󰋯', '|').replace('•', '|').replace('𐩒', '|').strip()
            keywords_en = re.sub('[\t\n]', '', pjt_keyword[1].text).replace('○', '|').replace('󰋯', '|').replace('•', '|').replace('𐩒', '|').strip()


            bus_tp=(pjt_id, bus_year, bus_name, bus_section, bus_agency, keywords)
    #         print(bus_tp)
            bus_sql = "INSERT INTO ntis_KM.business (pjt_id, bus_year, bus_name, bus_section, order_agency, keywords) values (%s, %s, %s, %s, %s, %s)"
            bus_curs.execute(bus_sql, bus_tp)
            conn.commit()
            bus_curs.close()
            bus_curs=conn.cursor()
            
            pjt_tp=(pjt_id, pjt_detail_num, pjt_name, pjt_detail_name, TPA, RMSA, TMO, pjt_name_ko, pjt_name_en, research_objective, research_content, expect_effect, keywords_ko, keywords_en, pjt_progress, practical_target, RnD_phase, RnD_main_agent, detailed_pjt_nature, RnD_nature, tech_life_cycle, location, CSTS, applied_field, pj_6T, NTRM, keywords)
            pjt_sql = "INSERT INTO ntis_KM.project (pjt_id, pjt_detail_num, pjt_name, pjt_detail_name, TPA, RMSA, TMO, pjt_name_ko, pjt_name_en, research_objective, research_content, expect_effect, keywords_ko, keywords_en, pjt_progress, practical_target, RnD_phase, RnD_main_agent, detailed_pjt_nature, RnD_nature, tech_life_cycle, location, CSTS, applied_field, 6T, NTRM, keywords) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            pjt_curs.execute(pjt_sql, pjt_tp)
            conn.commit()
            print("DB에 무사히 들어감")
            pjt_curs.close()
            pjt_curs = conn.cursor()
            
            fee_tp=(pjt_id, pjt_fee, bus_year,keywords)
    #         print(fee_tp)
            fee_sql="INSERT INTO ntis_KM.research_fee (pjt_id, fee, r_year, keywords) values(%s, %s, %s, %s)"
            fee_curs.execute(fee_sql, fee_tp)
            conn.commit()
            fee_curs.close()
            fee_curs=conn.cursor()

            #사업화 테이블 정보 수집
            commer_title=[]
            new_commer_text=[]
            commer_title=pjt_soup.select('div#divMain > div.pjt_status_wrap > div.outcome_wrap > div#outcomeTbl > div#tbl_rindust > table > tbody > tr > td.tl > a')
            try:
                if commer_title!="":
                    for d in range(len(commer_title)):
                        commer_title_text=re.sub('[\t\n]', '', commer_title[d].text).split('/')[0].strip()
                        if commer_title_text not in new_commer_text: 
                            if commer_title_text!="Private Research":
                                new_commer_text.append(commer_title_text)
                        if commer_title_text=="Private Research":
                            try:
                        # 사업화 클릭
                                delay=random.randrange(2,4)
                                sleep(delay)
                                private_xpath = """//*[@id="tbl_rindust"]/table/tbody/tr[%d]/td[2]/a""" % (d+1)
                                element = driver.find_element_by_xpath(private_xpath)
                                driver.execute_script("arguments[0].click();", element)

                            # 팝업창을 메인으로 변경
                                driver.switch_to.window(driver.window_handles[-1])
                                commer_html=driver.page_source
                                commer_soup=BeautifulSoup(commer_html, 'html.parser')
                                sleep(delay)

                            # 사업화 정보 긁어오기
                                commer_main = commer_soup.select('div#content > table')
                                commer_tr_td=commer_main[0].select('tr > td')
                                commercialization_name=commer_soup.select('div#content > div.roots_title2 > h3')
                                commercialization_name=commercialization_name[0].text
                                commercialization_name=re.sub('[\n\t]', '', commercialization_name).strip()
                                commercialization_year=commer_tr_td[0].text.strip()
                                commercialization_content=commer_tr_td[8].text.strip()
                                firm_name=commer_tr_td[2].text.strip()
                                representative_name=commer_tr_td[3].text.strip()
                                company_registration_num=re.sub('[\n\t]', '', commer_tr_td[4].text).strip()
                                bus_type_code=commer_tr_td[1].text.strip()
                                num_of_job_creation_people=commer_tr_td[5].text.strip()
                                sales_year=commer_tr_td[6].text.replace(',','').replace('원','').strip()
                                product_name=commer_tr_td[7].text.strip()
                                pjt_id=popup

                                #commercialization_num+=1
                            ########################################### 사업화 튜플 #########################################
                                com_tp = (pjt_id, commercialization_name, commercialization_content, firm_name, representative_name, company_registration_num, bus_type_code, num_of_job_creation_people, sales_year, product_name, commercialization_year) 
                                com_sql = "INSERT INTO ntis_KM.commercialization (pjt_id, commercialization_name, commercialization_content, firm_name, representative_name, company_registration_num, bus_type_code, num_of_job_creation_people, sales_year, product_name, commercialization_year) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                                print('---------------사업화-----------------')
                                print(com_tp)
                                driver.close()
                                com_curs.execute(com_sql , com_tp)
                                conn.commit()
                                com_curs.close()
                                com_curs=conn.cursor()

                            # 다시 팝업창으로 돌아오기
                                driver.switch_to.window(driver.window_handles[0])
                            except Exception as ex:
                                print(ex)
                        if d>=len(new_commer_text):
                            continue
                        else: 
                            try:
                                # 사업화 정보 url
                                # 검색 페이지 url
                                search_url_word = new_commer_text[d]
                                search_url_base = "https://www.ntis.go.kr/ThSearchResultIndustList.do?gubun=link&searchWord="
                                # 페이지 번호 url
                                search_url_sub = "&searchSentence=&searchType=&oldSearchWord="
                                search_url_sub2 = "&resultSearch=&pageNumber=1&ssoKnfSlct=0&ascDesc=ASC&useYn=N&oldQuery="
                                search_url_sub3 = "&oldAddQuery=I03%3D1%2FNOTSAME&pageYn=Y&downloadTarget=rindust&startRow=&endRow=&rqstPurpCd=&infoPrctuseDes=&sort=RANK%2FDESC&pageSize=100"

                                commer_url = search_url_base + search_url_word + search_url_sub + search_url_word + search_url_sub2 +  search_url_word + search_url_sub3 
                                # 사업화 제목에 맞춰 검색
                                driver.get(commer_url)
                                delay=random.randrange(2,4)
                                sleep(delay)
                                    
                                commer_search = driver.page_source
                                commer_soup1 = BeautifulSoup(commer_search, 'html.parser')
                                a_count=commer_soup1.select('div#content > div.sub_wrap > form#searchForm > div.list_box > div.resultBox > div > a')
                                for com_btn in range(len(a_count)):
                                    search_rf_name=re.sub('[\t\n]', '', a_count[com_btn].text).strip()
                                    if search_rf_name!=new_commer_text[d]:
                                        continue
                                    com_title_xpath = """//*[@id="searchForm"]/div[4]/div[2]/div[%d]/a""" % (com_btn+1)
                                    delay=random.randrange(2,4)
                                    sleep(delay)
                                    # 사업화 제목 클릭
                                    driver.find_element_by_xpath(com_title_xpath).click()
                                    driver.switch_to.window(driver.window_handles[-1])

                                    # 사업화 정보 긁어오기
                                    commer_html=driver.page_source
                                    commer_soup=BeautifulSoup(commer_html, 'html.parser')
                                    commer_main = commer_soup.select('div#content > table')
                                    commer_tr_td=commer_main[0].select('tr > td')
                                    commercialization_name=commer_soup.select('div#content > div.roots_title2 > h3')
                                    commercialization_name=commercialization_name[0].text
                                    commercialization_name=re.sub('[\n\t]', '', commercialization_name).strip()
                                    commercialization_year=commer_tr_td[0].text
                                    commercialization_content=commer_tr_td[8].text
                                    firm_name=commer_tr_td[2].text
                                    representative_name=commer_tr_td[3].text
                                    company_registration_num=re.sub('[\n\t]', '', commer_tr_td[4].text).strip()
                                    bus_type_code=commer_tr_td[1].text
                                    num_of_job_creation_people=commer_tr_td[5].text
                                    product_name=commer_tr_td[7].text.strip()
                                    sales_year=commer_tr_td[6].text.replace(',','').replace('원','')
                                    if sales_year!="-":
                                        sales_year=int(sales_year)

                                    #commercialization_num+=1
                                    ########################################### 사업화 튜플 #########################################
                                    com_tp = (pjt_id, commercialization_name, commercialization_content, firm_name, representative_name, company_registration_num, bus_type_code, num_of_job_creation_people, sales_year, product_name, commercialization_year)
                                    
                                    #print(com_tp)
                                    com_sql = "INSERT INTO ntis_KM.commercialization (pjt_id, commercialization_name, commercialization_content, firm_name, representative_name, company_registration_num, bus_type_code, num_of_job_creation_people, sales_year, product_name, commercialization_year) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                                    com_curs.execute(com_sql , com_tp)
                                    conn.commit()
                                    print('---------------사업화 잘 들어감-----------------')
                                    com_curs.close()
                                    com_curs=conn.cursor()
                                    driver.close()
                                    # 다시 메인창을 검색창으로 변경
                                    driver.switch_to.window(driver.window_handles[0])
                            except Exception as ex:
                                #driver.close()
                                print(ex)
            except Exception as ex:
                print(ex)
                
            #기술료 정보 테이블 수집
            try:
                search_rf = pjt_soup.select('#tbl_rtechnology > table > tbody > tr > td.tl > a')
                name_len=len(search_rf)
                name_list=[]
                rf_name_list=[]
                for rf_index in range(name_len):
                    name_list.append(re.sub('[\t\n]', '', search_rf[rf_index].text.split('/')[0]).strip())

                for name in name_list:
                    if name not in rf_name_list:
                        rf_name_list.append(name)
                    elif name=='Private Research':
                        rf_name_list.append(name)
                rf_name_len=len(rf_name_list)

                for rf_name_index in range(rf_name_len):
                    #Private Research 기술료 정보
                    if rf_name_list[rf_name_index]=='Private Research':
                        private_xpath = """//*[@id="tbl_rtechnology"]/table/tbody/tr/td[%d]/a"""%(rf_name_index+2)

                        element=driver.find_element_by_xpath(private_xpath)
                        driver.execute_script("arguments[0].click();", element)
                        driver.switch_to.window(driver.window_handles[-1])

                        private_html = driver.page_source
                        private_soup = BeautifulSoup(private_html, 'html.parser')

                        rf=private_soup.select('#content > table > tbody > tr > td')
                        rf_name=re.sub('[\t\n]', '', private_soup.select('#content > div > h3')[0].text).strip()

                        contract_year=rf[0].text
                        contract_date=rf[1].text
                        target_country=re.sub('[\t\n]','',rf[2].text).strip()
                        implementation_method=rf[3].text
                        target_organization=rf[4].text
                        company_registration_num=re.sub('[\t\n]', '', rf[5].text).strip()
                        this_year_accrual=re.findall('[0-9,]+', rf[6].text)[0].replace(',','')
                        fees_paid_by_the_government=rf[7].text
                        total_private_research_expense=re.findall('[0-9,]+', rf[8].text)[0].replace(',','')
                        total_government_contributions=re.findall('[0-9,]+', rf[9].text)[0].replace(',','')
                        payment_method=rf[10].text
                        developent_agency=rf[11].text
                        implementation_contents=rf[12].text

                        #rf_num+=1
                        rf_tp=(pjt_id,rf_name,contract_year,contract_date,target_country,implementation_method,target_organization,company_registration_num,this_year_accrual,fees_paid_by_the_government,total_private_research_expense,total_government_contributions,payment_method,developent_agency,implementation_contents)
                        print('---------------기술료-----------------')
                        print(rf_tp)
                        rf_sql = "INSERT INTO ntis_KM.royalty_fee (pjt_id,rf_name,contract_year,contract_date,target_country,implementation_method,target_organization,company_registration_num,this_year_accrual,fees_paid_by_the_government,total_private_research_expense,total_government_contributions,payment_method,developent_agency,implementation_contents) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        rf_curs.execute(rf_sql, rf_tp)
                        conn.commit()
                        rf_curs.close()
                        rf_curs=conn.cursor()
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    else:
                        search_rf_url="https://www.ntis.go.kr/ThSearchResultTechnologyList.do?sort=RANK%2FDESC&ntisYn=&searchWord="
                        search_rf_sub ="&pageSize=20"
                        driver.get(search_rf_url+rf_name_list[rf_name_index]+search_rf_sub)
                        search_rf_html = driver.page_source
                        search_rf_soup = BeautifulSoup(search_rf_html, 'html.parser')

                        search_rf_result=search_rf_soup.select('#searchForm > div.list_box > div.resultBox > div > a')
                        search_rf_len=len(search_rf_result)
                        for search_rf_index in range(search_rf_len):
                            search_rf_name=re.sub('[\t\n]', '', search_rf_result[search_rf_index].text).strip()
                            if search_rf_name!=rf_name_list[rf_name_index]:
                                continue
                            delay = random.randrange(4,6)
                            sleep(delay)
                            rf_xpath = """//*[@id="searchForm"]/div[4]/div[2]/div[%d]/a"""%(search_rf_index+1)
                            driver.find_element_by_xpath(rf_xpath).click()
                            driver.switch_to.window(driver.window_handles[-1])

                            pop_up=True
                            rf_html = driver.page_source
                            rf_soup = BeautifulSoup(rf_html, 'html.parser')

                            rf_name=rf_name_list[rf_name_index]
                            rf=rf_soup.select('#content > table > tbody > tr > td')
                            contract_year=rf[0].text
                            contract_date=rf[1].text
                            target_country=re.sub('[\t\n]','',rf[2].text).strip()
                            implementation_method=rf[3].text
                            target_organization=rf[4].text
                            company_registration_num=re.sub('[\t\n]', '', rf[5].text).strip()
                            this_year_accrual=re.findall('[0-9,]+', rf[6].text)[0].replace(',','')
                            fees_paid_by_the_government=rf[7].text
                            total_private_research_expense=re.findall('[0-9,]+', rf[8].text)[0].replace(',','')
                            total_government_contributions=re.findall('[0-9,]+', rf[9].text)[0].replace(',','')
                            payment_method=rf[10].text
                            developent_agency=rf[11].text
                            implementation_contents=rf[12].text
                            #rf_num+=1
                            rf_tp=(pjt_id,rf_name,contract_year,contract_date,target_country,implementation_method,target_organization,company_registration_num,this_year_accrual,fees_paid_by_the_government,total_private_research_expense,total_government_contributions,payment_method,developent_agency,implementation_contents)
                            print('---------------기술료-----------------')
                            print(rf_tp)
                            rf_sql = "INSERT INTO ntis_KM.royalty_fee (pjt_id,rf_name,contract_year,contract_date,target_country,implementation_method,target_organization,company_registration_num,this_year_accrual,fees_paid_by_the_government,total_private_research_expense,total_government_contributions,payment_method,developent_agency,implementation_contents) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                            rf_curs.execute(rf_sql, rf_tp)
                            conn.commit()
                            rf_curs.close()
                            rf_curs=conn.cursor()
                            driver.close()
                            pop_up=False
                            driver.switch_to.window(driver.window_handles[0])              
            except Exception as ex:
                print(ex)
                #if pop_up==True:
                    #print('팝업창')
                    #driver.close()
                    #pop_up=False
                    #drvier.switch_to.window(driver.window_handles[0])
                #else:
                    #print(ex)
        except Exception as ex:
            print(ex)