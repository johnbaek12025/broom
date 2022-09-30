# broomstick

crawling coupang, gmarket, auction
   1. 프로그램 설명

## 실행방식

1. git 설치
```
https://git-scm.com/
```

2. broomstick 프로그램 설치
```
git clone https://github.com/johnbaek12025/broomstick
```

3. Python 3.8 설치
```
https://www.python.org/downloads/
```

4. 라이브러리 설치
- 파이썬 라이브러리
```
pip install -r requirements.txt
```
5. broomstick/examples 에 있는 exemple.cfg 를 수정하여서 특정 폴더에 저장
```
Ex) broomstick/cfg/bs_config.cfg
```
6. data_save folder 생성
```
Made a interruption for saving current postion of vendor and data in this folder
when stoping this application while is being executed.
```

7. Unit-test 를 실행하여 문제 없는지 확인
```
- unit-test 필요함!!!
```
8. 실행
```
# 옵션 파일이 broomstick/cfg 아래에 위치하고, 콘텐츠 이름이 coupang 일 경우
cd bin
../bin/python bs.py --content=coupang --config=../cfg/bs_config.cfg
```
