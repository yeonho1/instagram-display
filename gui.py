import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from urllib.request import urlopen
import ssl
import json
import threading
import time
import webbrowser


class Communicate(QObject):
    signal = pyqtSignal(dict)

class Comm2(QObject):
    signal = pyqtSignal(int)

# 인스타그램 API에서 5초마다 정보를 얻어오는 쓰레드
class InstagramInfoThread(threading.Thread):
    def __init__(self, username, callbackFunc, *args, **kwargs):
        super(InstagramInfoThread, self).__init__(*args, **kwargs)
        # 변수 기본값 설정
        self.username = username
        self.stopped = False
        self.context = ssl._create_unverified_context()
        self.fullname = None
        self.biography = None
        self.followers = None
        self.following = None
        self.posts = None
        self.profileImg = None
        self.communicate = Communicate()
        self.callbackFunc = callbackFunc
    def stop(self):
        # 쓰레드 정지 코드
        self.stopped = True
    def run(self):
        self.communicate.signal.connect(self.callbackFunc) # GUI 프로그램과 통신할 수 있게 한다
        while not self.stopped: # 정지하지 않은 때동안
            try:
                # 주어진 아이디를 토대로 정보를 가지고 온다
                url = f'https://www.instagram.com/{self.username}/?__a=1'
                result = urlopen(url, context=self.context).read()
                data = json.loads(result)
                self.fullname = data['graphql']['user']['full_name']
                # self.username = data['graphql']['user']['username']
                self.biography = data['graphql']['user']['biography']
                self.followers = int(data['graphql']['user']['edge_followed_by']['count'])
                self.following = int(data['graphql']['user']['edge_follow']['count'])
                self.posts = int(data['graphql']['user']['edge_owner_to_timeline_media']['count'])
                self.profileImg = data['graphql']['user']['profile_pic_url_hd']
                # self.log_info(fullname,username,biography,followers,following,posts)
            except Exception as e:
                self.fullname = None
                self.username = None
                self.biography = None
                self.followers = None
                self.following = None
                self.posts = None
                self.profileImg = None
                print(e)
            # 얻은 정보를 GUI 프로그램으로 보낸다
            msg = {
                'fullname':self.fullname,
                'username':self.username,
                'biography':self.biography,
                'followers':self.followers,
                'following':self.following,
                'posts':self.posts,
                'profileImg':self.profileImg
            }
            self.communicate.signal.emit(msg)
            count = 0
            while count <= 500:
                time.sleep(0.01)
                if self.stopped:
                    break
                count += 1
            else:
                continue
            break
        print(f'{threading.currentThread().getName()} stopped')
    # 디버깅을 위해 정보를 출력하는 코드
    def log_info(self, fullname, username, biography, followers, following, posts):
        print(f'{username} ({fullname})')
        print('-----Biography-----')
        print(biography)
        print('-----INFO-----')
        print(f'{followers} Followers {following} Following {posts} Posts')
# 게시물을 표시하는 창 (개발 중지)
"""
class PostsWindow(QMainWindow):
    def __init__(self, username, callbackFunc, parent=None):
        super(PostsWindow, self).__init__(parent)
        self.username = username
        self.setWindowTitle(f'@{self.username} - 게시물')
        self.setGeometry(300,300,640,840)
        self.setWindowResizable(False)
        self.communicate = Comm2()
        self.communicate.signal.connect(callbackFunc)

    def closeEvent(self, event):
        self.communicate.signal.emit(1)
        event.accept()
"""

# 본 윈도우 (프로필사진, 팔로워,팔로잉,게시물 표시)
class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Instagram Display 1.0")
        self.setGeometry(1000, 1000, 1060, 540)
        # self.setStyleSheet("QLabel {font: 30pt}")
        self.isSecondClosed = True
        self.img = QLabel(self)
        self.img.resize(500, 500)
        self.img.move(20, 20)
        self.id = QLabel("인스타그램 아이디", self)
        self.id.move(540, 20)
        self.id.setGeometry(QRect(540,20,1040,60))
        self.id.setStyleSheet("font: 50pt")
        self.biography = QTextEdit(self)
        self.biography.setReadOnly(True)
        self.biography.setLineWrapMode(QTextEdit.NoWrap)
        font = self.biography.font()
        font.setPointSize(10)
        self.biography.move(540,100)
        self.biography.setGeometry(QRect(540,100,500,160))
        self.followers = QLabel("팔로워", self)
        self.followers.move(540,180)
        self.followers.setStyleSheet("font: 30pt")
        self.followers.setGeometry(QRect(540,180,1040,210))
        self.following = QLabel("팔로잉", self)
        self.following.move(540, 210)
        self.following.setStyleSheet("font: 30pt")
        self.following.setGeometry(QRect(540,210,1040,240))
        self.posts = QLabel("게시물", self)
        self.posts.move(540, 240)
        self.posts.setStyleSheet("font: 30pt")
        self.posts.setGeometry(QRect(540,240,1040,270))
        self.button = QPushButton("게시물 보기", self)
        self.button.move(540, 410)
        self.button.clicked.connect(self.showPosts)
        self.context = ssl._create_unverified_context()

    # 쓰레드로부터 데이터가 들어왔을 때 표시
    def dataCallback(self, msg):
        if msg['followers']:
            followers = msg['followers']
            self.followers.setText(f'팔로워 {followers}명')
        else:
            self.followers.setText('팔로워 정보없음')
        if msg['following']:
            following = msg['following']
            self.following.setText(f'팔로잉 {following}명')
        else:
            self.following.setText('팔로잉 정보없음')
        if msg['profileImg']:
            profileImg = msg['profileImg']
            image = urlopen(profileImg, context=self.context).read()
            pixmap = QPixmap()
            pixmap.loadFromData(image)
            pixmap = pixmap.scaledToHeight(500)
            self.img.setPixmap(pixmap)
        else:
            self.img.setText('프로필사진 정보없음')
        if msg['username']:
            self.username = msg['username']
            self.id.setText(f'@{self.username}')
        else:
            self.id.setText('아이디 정보없음')
        if msg['biography']:
            biography = msg['biography']
            self.biography.setText(biography)
        else:
            self.biography.setText('소개글 정보없음')
        if msg['posts']:
            posts = msg['posts']
            self.posts.setText(f'게시물 {posts}개')
        else:
            self.posts.setText('게시물 정보없음')

    # 닫힐 때 쓰레드 정지하고 종료
    def closeEvent(self, event):
        self.thread.stop()
        event.accept()
    """
    def secondClose(self, integer):
        if integer == 1:
            self.isSecondClosed = True
    """


    # 시작 시 아이디 물어보기
    def popup(self):
        text, ok = QInputDialog.getText(self, 'Instagram Display 1.0', '환영합니다!\n우선 인스타그램 닉네임을 알려주십시오.')
        if ok:
            text = text.strip()
            if text != '':
                self.thread = InstagramInfoThread(text, self.dataCallback, name='Instagram Display')
                self.thread.start()
            else:
                msg = QMessageBox()
                msg.setWindowTitle("오류")
                msg.setStyleSheet("font: 12pt")
                msg.setText("인스타그램 아이디를 제대로 입력해주십시오.")
                msg.setIcon(QMessageBox.Icon.Warning)
                x = msg.exec_()
                self.popup()
        else:
            msg = QMessageBox()
            msg.setWindowTitle("오류")
            msg.setText("인스타그램 아이디를 입력해주십시오.")
            msg.setIcon(QMessageBox.Icon.Warning)
            x = msg.exec_()
            self.popup()

    # 게시물 표시 (브라우저 띄음)
    def showPosts(self):
        """
        if self.isSecondClosed:
            self.postsWindow = PostsWindow(self.username, self.secondClose, self)
            self.postsWindow.show()
            self.isSecondClosed = False
        else:
            msg = QMessageBox()
            msg.setWindowTitle("오류")
            msg.setText("창이 이미 열려있습니다.")
            msg.setIcon(QMessageBox.Icon.Warning)
            x = msg.exec_()
        """
        webbrowser.open('https://www.instagram.com/yeonho_08/', new=1, autoraise=True)

# import한 경우가 아니라 직접 실행한 경우 GUI까지 띄움
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    myWindow.popup()
    app.exec_()
