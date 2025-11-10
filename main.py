import sys
import asyncio
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QProgressDialog
)
from PyQt6.QtCore import Qt
from panel import Ui_MainWindow
from qasync import QEventLoop, asyncSlot
from func import telegram_panel
from code_dialog import CodeDialog, AsyncMessageBox
from pyrogram import (Client,errors,enums)
import os, random, shutil, sqlite3, traceback
from datetime import datetime

os.makedirs('data', exist_ok=True)
os.makedirs('account', exist_ok=True)
os.makedirs('gaps', exist_ok=True)
os.makedirs('delete', exist_ok=True)


Status = False
Extract = False
Members_ext = []
Members = []
Okm , Badm = 0 , 0
Runs,Final = [],[]
max_runed = telegram_panel.get_max_concurrent()
print("Max Run Threads:", max_runed)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setFixedSize(self.size())
        self.acclistupdate()
        self.update_list_group_remove()
        self.ui.add_account.clicked.connect(self.add_account_proc)
        self.ui.remove_account_bot.clicked.connect(self.remove_account)
        self.ui.update_number_bot.clicked.connect(self.acclistupdate)
        self.ui.extract_bot.clicked.connect(self.extract_group)
        self.ui.stop_extract.clicked.connect(self.disable_extract_group)
        self.ui.rem_extract_bot.clicked.connect(self.remove_extract_group)
        # self.ui.number_add_bot.setReadOnly(True)
        self.ui.number_add_bot.setMaximum(30)
        self.ui.tab_account.currentChanged.connect(self.update_list_tab)
        self.ui.update_list_gaps.clicked.connect(self.update_listgroupload)
        self.ui.load_member_bot.clicked.connect(self.load_member)
        self.ui.clear_load_bot.clicked.connect(self.clear_load)
        self.ui.start_adder_bot.clicked.connect(self.start_adder)
        self.ui.stop_adder_bot.clicked.connect(self.stop_adder)
        self.ui.save_log_bot.clicked.connect(self.save_log)

    
    
    
    def update_list_tab(self, index):
        if index == 0:
            r = telegram_panel.list_accounts()
            self.ui.list_account_ac.clear()
            self.ui.list_account_ac.addItems(r)
            self.ui.lcdNumber.display(len(r))
        if index == 1:
            r = telegram_panel.list_groups()
            self.ui.list_group_rem.clear()
            self.ui.list_group_rem.addItems(r)
        if index == 2:
            r = telegram_panel.list_groups()
            self.ui.list_group_load.clear()
            self.ui.list_group_load.addItems(r)
            self.ui.number_acc_add.setMaximum(len(telegram_panel.list_accounts()))
        return
    
    
    def update_listgroupload(self):
        r = telegram_panel.list_groups()
        self.ui.list_group_load.clear()
        self.ui.list_group_load.addItems(r)
        QMessageBox.information(self, "Success", "Group list updated.")
        return
    
    
    def load_member(self):
        global Members
        if Status:
            QMessageBox.critical(self, "Error", "Adding is active.")
            return
        R = self.ui.list_group_load.currentText()
        for i in telegram_panel.load_group(R):
            if i not in Members:
                Members.append(i)
        self.ui.lcdNumber_load.display(len(Members))
        QMessageBox.information(self, "Success", "Group members loaded.")
        return
    
    
    def clear_load(self):
        global Members, Status
        if Status:
            QMessageBox.critical(self, "Error", "Adding is active.")
            return
        Members = []
        self.ui.lcdNumber_load.display(len(Members))
        QMessageBox.information(self, "Success", "Group members cleared.")
        return
    
    
    def stop_adder(self):
        global Status
        if Status:
            QMessageBox.information(self, "Success", "Adding stopped.")
            Status = False
        else:
            QMessageBox.critical(self, "Error", "Adding is not active.")
        return
    
    
    @asyncSlot()
    async def ask_code_dialog(self, title, label):
        dlg = CodeDialog(title, label, self)
        dlg.setModal(True)
        dlg.show()
        while dlg.result() == 0:  # QDialog.DialogCode.Rejected = 0, Accepted = 1
            await asyncio.sleep(0.1)

        if dlg.result() == 1:
            return dlg.get_value(), True
        else:
            return "", False
    
    
    @asyncSlot()
    async def show_async_message(self, title, message, icon=QMessageBox.Icon.Information):
        dlg = AsyncMessageBox(title, message, icon, self)
        dlg.show()

        while dlg.result is None:
            await asyncio.sleep(0.05)

        return dlg


    def do_long_task(self):
        dlg = QProgressDialog("Processing ...", None, 0, 0, self)
        dlg.setWindowTitle("Please wait.")
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.setMinimumDuration(0)
        dlg.show()
        return dlg


    @asyncSlot()
    async def add_account_proc(self):
        phone = self.ui.account_input_add.text().strip()

        if len(phone) < 4:
            # QMessageBox.critical(self, "Wrong", "Phone number is too short.")
            await self.show_async_message("Wrong", "Phone number is too short.", icon=QMessageBox.Icon.Critical)

            return

        if not phone.startswith("+") or not phone[1:].isdigit():
            # QMessageBox.critical(self, "Wrong", "Phone number must start with '+' and contain only digits after it.")
            await self.show_async_message("Wrong", "Phone number must start with '+' and contain only digits after it.", icon=QMessageBox.Icon.Critical)
            return

        if phone == "+123456789":
            # QMessageBox.critical(self, "Wrong", "Sample phone number is not allowed.")
            await self.show_async_message("Wrong", "Sample phone number is not allowed.", icon=QMessageBox.Icon.Critical)
            return

        dlg = self.do_long_task()
        r = await telegram_panel.add_account(phone)
        dlg.close()

        if not r["status"]:
            # QMessageBox.critical(self, "Error", r["message"])
            await self.show_async_message("Error", str(r["message"]), icon=QMessageBox.Icon.Critical)
            return

        # ورود کد
        for _ in range(3):
            # text, ok = QInputDialog.getText(self, "Account login code", "Enter the 5-digit code:")
            text, ok = await self.ask_code_dialog( "Account login code", "Enter the 5-digit code:")
            for _ in range(10):
                if not ok:
                    break
                if text.isdigit() and len(text) == 5:
                    break
                else:
                    # text, ok = QInputDialog.getText(self, "Account login code", "Enter the 5-digit code:")
                    text, ok = await self.ask_code_dialog( "Account login code", "Enter the 5-digit code:")

            if not ok:
                await telegram_panel.cancel_acc(r["cli"], r["phone"])
                # QMessageBox.critical(self, "Error", "Canceled by user.")
                await self.show_async_message("Error", "Canceled by user.", icon=QMessageBox.Icon.Critical)
                return

            dlg = self.do_long_task()
            rs = await telegram_panel.get_code(r["cli"], r["phone"], r["code_hash"], text)
            dlg.close()

            if rs["status"]:
                # QMessageBox.information(self, "Success", rs["message"])
                await self.show_async_message("Success", rs["message"], icon=QMessageBox.Icon.Information)
                telegram_panel.make_json_data(r["phone"], r["api_id"], r["api_hash"], r["proxy"], "")
                return

            if rs["message"] == "invalid_code":
                # QMessageBox.critical(self, "Error", "Invalid code.")
                await self.show_async_message("Error", "Invalid code.", icon=QMessageBox.Icon.Critical)
                continue

            if rs["message"] == "FA2":
                for _ in range(3):
                    # text, ok = QInputDialog.getText(self, "Account password", "Enter the password:")
                    text, ok = await self.ask_code_dialog("Account password", "Enter the password:")
                    if not ok:
                        await telegram_panel.cancel_acc(r["cli"], r["phone"])
                        # QMessageBox.critical(self, "Error", "Canceled by user.")
                        await self.show_async_message("Error", "Canceled by user.", icon=QMessageBox.Icon.Critical)
                        return

                    dlg = self.do_long_task()
                    rsp = await telegram_panel.get_password(r["cli"], r["phone"], text)
                    dlg.close()

                    if rsp["status"]:
                        # QMessageBox.information(self, "Success", rsp["message"])
                        await self.show_async_message("Success", rsp["message"], icon=QMessageBox.Icon.Information)
                        telegram_panel.make_json_data(r["phone"], r["api_id"], r["api_hash"], r["proxy"], text)
                        return

                    if rsp["message"] == "invalid_password":
                        # QMessageBox.critical(self, "Error", "Invalid password.")
                        await self.show_async_message("Error", "Invalid password.", icon=QMessageBox.Icon.Critical)
                        continue
                    else:
                        # QMessageBox.critical(self, "Error", rsp["message"])
                        await self.show_async_message("Error", rsp["message"], icon=QMessageBox.Icon.Critical)
                        return

            if rs["message"]:
                # QMessageBox.critical(self, "Error", rs["message"])
                await self.show_async_message("Error", rs["message"], icon=QMessageBox.Icon.Critical)
                return

        try:await telegram_panel.cancel_acc(r["cli"], r["phone"])
        except:pass
        # QMessageBox.critical(self, "Error", "Canceled by user.")
        await self.show_async_message("Error", "Canceled by user.", icon=QMessageBox.Icon.Critical)
        return

    def remove_account(self):
        phone = self.ui.remove_account_input.text().strip()
        if phone in telegram_panel.list_accounts():
            telegram_panel.remove_account(phone)
            QMessageBox.information(self, "Success", "Account removed.")
        else:
            QMessageBox.critical(self, "Error", "Account not found.")
        return
    

    def acclistupdate(self,log=True):
        r = telegram_panel.list_accounts()
        self.ui.list_account_ac.clear()
        self.ui.list_account_ac.addItems(r)
        self.ui.lcdNumber.display(len(r))
        if not log:
            QMessageBox.information(self, "Success", "Account list updated.")
        return
    
    
    def update_list_group_remove(self):
        self.ui.list_group_rem.clear()
        self.ui.list_group_rem.addItems(telegram_panel.list_groups())
        return
    
    
    @asyncSlot()
    async def disable_extract_group(self):
        global Extract
        if Extract:
            Extract = False
            self.ui.status_extract.setText("Status: Inactive")
            # QMessageBox.information(self, "Success", "Extraction stopped.")
            await self.show_async_message("Success", "Extraction stopped.", icon=QMessageBox.Icon.Information)
        else:
            # QMessageBox.critical(self, "Error", "Extraction is not active.")
            await self.show_async_message("Error", "Extraction is not active.", icon=QMessageBox.Icon.Critical)
        return
    
    
    @asyncSlot()
    async def extract_group(self):
        global Extract
        
        self.ui.log_extract.clear()
        self.ui.log_extract.setReadOnly(True)
        
        if len(telegram_panel.list_accounts()) == 0:
            # QMessageBox.critical(self, "Error", "No accounts found.")
            await self.show_async_message("Error", "No accounts found.", icon=QMessageBox.Icon.Critical)
            return
        if Extract:
            # QMessageBox.critical(self, "Error", "Already extracting.")
            await self.show_async_message("Error", "Already extracting.", icon=QMessageBox.Icon.Critical)
            return
        link = self.ui.group_extracct_input.text().strip()
        if telegram_panel.is_valid_telegram_link(link):
            Extract = True
            self.ui.status_extract.setText("Status: Active")
            asyncio.create_task(self.extract_proc(link))
        else:
            # QMessageBox.critical(self, "Error", "Invalid Telegram link.")
            await self.show_async_message("Error", "Invalid Telegram link.", icon=QMessageBox.Icon.Critical)
        return
    
    
    async def extract_proc(self, link):
        global Extract, Members_ext
        
        phone = random.choice(telegram_panel.list_accounts())
        
        self.ui.log_extract.appendPlainText("Extracting {}...".format(phone))
        data = telegram_panel.get_json_data(phone)
        proxy = await telegram_panel.get_proxy(data["proxy"])
        cli = Client('account/{}'.format(phone), data["api_id"], data["api_hash"], proxy=proxy[0])
        await asyncio.wait_for(cli.connect() , 15)
        self.ui.log_extract.appendPlainText("Connected to {}.".format(phone))
        join = await telegram_panel.Join(cli,link)
        if len(join) != 3:
            Extract = False
            try:await cli.disconnect()
            except:pass
            # QMessageBox.critical(self, "Error", "Failed to join the group.")
            self.ui.log_extract.appendPlainText("Failed to join the group.\n{}".format(join[0]))
            await self.show_async_message("Error", "Failed to join the group.", icon=QMessageBox.Icon.Critical)
            return
        chat= await cli.get_chat(join[0])
        count = chat.members_count
        self.ui.log_extract.appendPlainText("Number of chat members: {}".format(count))
        Members_ext = []
        serch = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z','0', '1', '2', '3', '4', '5', '6', '7', '8', '9',"🔥", "❤️", "✨", "🌹", "😊", "🎉", "💖", "😎", "🌈", "⚡", "👑", "🖤",'ा', 'क', 'े', 'र', 'ह', 'स', 'न', 'ी', 'ं', 'म']
        async for result in cli.get_chat_members(chat.id,limit=count,filter=enums.ChatMembersFilter.RECENT):
            try:
                if Extract == False:
                    break
                item = result.user
                if result.status == enums.ChatMemberStatus.MEMBER:
                    if item.is_bot != True and item.username != None:
                        if item.username not in Members_ext:
                            Members_ext.append(item.username)
                            self.ui.list_ex.addItem(item.username)
                            self.ui.lcdNumber_member_extract.display(len(Members_ext))
                            self.ui.log_extract.appendPlainText("[{}] {}".format(len(Members_ext),item.username))
                            await asyncio.sleep(0.1)
            except Exception as e:
                traceback.print_exc()
                
        for sq in serch:
            if Extract == False:
                break
            async for result in cli.get_chat_members(chat.id,sq,count,filter=enums.ChatMembersFilter.SEARCH):
                try:
                    if Extract == False:
                        break
                    item = result.user
                    if result.status == enums.ChatMemberStatus.MEMBER:
                        if item.is_bot != True and item.username != None:
                            if item.username not in Members_ext:
                                Members_ext.append(item.username)
                                self.ui.log_extract.appendPlainText("[{}] {}".format(len(Members_ext),item.username))
                except Exception as e:
                    traceback.print_exc()

        Extract = False
        self.ui.status_extract.setText("Status: Disactive")
        await cli.disconnect()
        self.ui.log_extract.appendPlainText("Disconnected from {}.".format(phone))
        if len(Members_ext) != 0:
            with open('gaps/{}.txt'.format(link.split('/')[-1] if not link.startswith("@") else link[1:]),'w',encoding='utf-8') as f:
                f.write('\n'.join(Members_ext))
        self.ui.log_extract.appendPlainText("Extracted {} members.".format(len(Members_ext)))
        await self.show_async_message("Success", "Extracted {} members.".format(len(Members_ext)), icon=QMessageBox.Icon.Information)
        try:self.update_list_group_remove()
        except:pass
        return
    
    
    def remove_extract_group(self):
        try:
            os.remove('gaps/{}.txt'.format(self.ui.list_group_rem.currentText()))
            self.update_list_group_remove()
            QMessageBox.information(self, "Success", "Extracted group removed.")
        except:
            QMessageBox.critical(self, "Error", "Extracted group not found.")
        return
    
    
    # async def run_adder(self):
    #     global Status , Members , Okm , Badm, Runs , Final, max_runed
        
    #     link = self.ui.input_link_add.text()
    #     number_add , number_account = self.ui.number_add_bot.value() , self.ui.number_acc_add.value()
        
    #     Runs, Final = [],[]
        
    #     accs = telegram_panel.list_accounts()
    #     lsacc = random.sample(accs, number_account if number_account < len(accs) else len(accs))
        
    #     while True:
    #         if Status == False:
    #             break
    #         try:self.ui.ok_number.display(Okm)
    #         except:pass
    #         try:self.ui.bad_number.display(Badm)
    #         except:pass
    #         try:self.ui.acc_complate_number.display(Final)
    #         except:pass
    #         try:self.ui.lcdNumber_load.display(len(Members))
    #         except:pass
    #         if len(Runs) < max_runed and len(lsacc) != 0:
    #             try:
    #                 phone = lsacc.pop()
    #                 Runs.append(phone)
    #                 asyncio.create_task(self.adder_account(phone, link, number_add))
    #                 self.ui.log_adder.appendPlainText(self.get_time()+"Run adder c! - Account: "+phone)
    #             except Exception as e:
    #                 print(e)
    #                 try:
    #                     x = phone
    #                     if phone in Runs:Runs.remove(phone)
    #                     if phone not in Final:Final.append(phone)
    #                 except:x = "Unknown"
    #                 self.ui.log_adder.appendPlainText(self.get_time()+"Run adder c! - Error: "+str(e)+" - Account: "+x)
            
    #         if number_account == len(Final):
    #             break
            
    #         await asyncio.sleep(1)
        
        
    #     self.ui.log_adder.appendPlainText(self.get_time()+"Finished.")
    #     await self.show_async_message("Success", "Adding Finished.", icon=QMessageBox.Icon.Information)
    #     Status = False
    #     self.ui.log_adder.appendPlainText("Status: Disactive")
    #     self.ui.input_link_add.setReadOnly(False)
    #     self.ui.number_add_bot.setReadOnly(False)
    #     self.ui.number_acc_add.setReadOnly(False)

    #     return
            
    async def run_adder(self):
        global Status, Members, Okm, Badm, Runs, Final, max_runed

        link = self.ui.input_link_add.text()
        number_add, number_account = self.ui.number_add_bot.value(), self.ui.number_acc_add.value()

        Runs, Final = [], []
        accs = telegram_panel.list_accounts()
        lsacc = random.sample(accs, number_account if number_account < len(accs) else len(accs))

        sem = asyncio.Semaphore(max_runed)
        tasks = []

        async def limited_adder(phone):
            async with sem:
                try:
                    Runs.append(phone)
                    await self.adder_account(phone, link, number_add)
                finally:
                    if phone in Runs:
                        Runs.remove(phone)
                    if phone not in Final:
                        Final.append(phone)

        for phone in lsacc:
            tasks.append(asyncio.create_task(limited_adder(phone)))
            self.ui.log_adder.appendPlainText(self.get_time() + "Run adder started - Account: " + phone)

        await asyncio.gather(*tasks)

        self.ui.log_adder.appendPlainText(self.get_time() + "Finished.")
        await self.show_async_message("Success", "Adding Finished.", icon=QMessageBox.Icon.Information)
        Status = False
        self.ui.log_adder.appendPlainText("Status: Disactive")
        self.ui.input_link_add.setReadOnly(False)
        self.ui.number_add_bot.setReadOnly(False)
        self.ui.number_acc_add.setReadOnly(False)
    
    async def adder_account(self, phone: str , link: str , number_add: int):
        global Status , Members , Okm , Badm, Runs , Final
        if Status == False:
            return False

        try:
            self.ui.log_adder.appendPlainText(self.get_time()+"Starting Account: "+phone)
            data = telegram_panel.get_json_data(phone)
            proxy = await telegram_panel.get_proxy(data["proxy"])
            cli = Client('account/{}'.format(phone), data["api_id"], data["api_hash"], proxy=proxy[0])
            await asyncio.wait_for(cli.connect() , 15)
            self.ui.log_adder.appendPlainText(self.get_time()+"Connected to account: "+phone)
            
            chat = await telegram_panel.Join(cli,int(link))
            if len(chat) == 3:
                self.ui.log_adder.appendPlainText(self.get_time()+"Joined to chat: "+link)
                await asyncio.sleep(1)
                chdy = await cli.get_chat(chat[0])
                countmembers = chdy.members_count
                self.ui.log_adder.appendPlainText(self.get_time()+"Members count: "+str(countmembers))
                await asyncio.sleep(1)
                if countmembers > 200:
                    try:await cli.disconnect()
                    except:pass
                    self.ui.log_adder.appendPlainText(self.get_time()+"The channel has more than 200 members. The adding has been stopped.")
                    await self.show_async_message("Error", "The channel has more than 200 members. The adding has been stopped.", icon=QMessageBox.Icon.Critical)
                    Status = False
                    return
                numadd = 0
                error_count = 0
                OK,BAD = 0,0
                while True:
                    if error_count > 5:
                        break
                    if Status == False:
                        break
                    if numadd == number_add:
                        break
                    if len(Members) == 0:
                        Status = False
                        self.ui.log_adder.appendPlainText(self.get_time()+"Users list is empty.")
                        break
                    try:
                        randuser = random.choice(Members)
                        Members.remove(randuser)
                        await cli.add_chat_members(chat[0] , randuser)
                        Okm += 1
                        numadd += 1
                        OK += 1
                        self.ui.ok_number.display(Okm)
                        self.ui.log_adder.appendPlainText(self.get_time()+"Added: "+randuser)
                    except (errors.exceptions.not_acceptable_406.ChannelPrivate ) as er:
                        Status = False
                        self.ui.log_adder.appendPlainText(self.get_time()+"The channel is unavailable! The adding has been stopped. - Error: "+str(er)+ " - Account: "+phone)
                        error_count += 1
                        break
                    except (errors.SessionExpired , errors.SessionRevoked , errors.UserDeactivatedBan , errors.UserDeactivated) as er:
                        try:Members.append(randuser)
                        except:pass
                        try:await cli.disconnect()
                        except:pass
                        try:shutil.move("account/{}.session".format(phone) , "delete/{}.session".format(phone))
                        except:pass
                        try:shutil.move("data/{}.json".format(phone) , "delete/{}.json".format(phone))
                        except:pass
                        self.ui.log_adder.appendPlainText(self.get_time()+"The account has been banned! The adding has been stopped. - Error: "+str(er)+ " - Account: "+phone)
                        error_count += 1
                        if phone in Runs:Runs.remove(phone)
                        if phone not in Final:Final.append(phone)
                        return
                    except errors.UsernameNotOccupied as er:
                        try:Members.append(randuser)
                        except:pass
                        try:await cli.disconnect()
                        except:pass
                        try:shutil.move("account/{}.session".format(phone) , "delete/{}.session".format(phone))
                        except:pass
                        try:shutil.move("data/{}.json".format(phone) , "delete/{}.json".format(phone))
                        except:pass
                        self.ui.log_adder.appendPlainText(self.get_time()+"The account has been freez! The adding has been stopped. - Error: "+str(er)+ " - Account: "+phone)
                        error_count += 1
                        if phone in Runs:Runs.remove(phone)
                        if phone not in Final:Final.append(phone)
                        return
                    except errors.UserPrivacyRestricted as er:
                        self.ui.log_adder.appendPlainText(self.get_time()+"The user ["+randuser+"] has privacy restrictions! - Account: "+phone)
                        Badm += 1
                        BAD += 1
                    except errors.ChatMemberAddFailed as er:
                        self.ui.log_adder.appendPlainText(self.get_time()+"The user ["+randuser+"] has ChatMemberAddFailed! - Account: "+phone)
                        Badm += 1
                        BAD += 1
                    except errors.FloodWait as e:
                        try:Members.append(randuser)
                        except:pass
                        self.ui.log_adder.appendPlainText(self.get_time()+"FloodWait: "+str(e.value)+" - Account: "+phone)
                        if int(e.value) < 500:
                            await asyncio.sleep(int(e.value)+ random.randint(5,25))
                        else:
                            break
                    except (TimeoutError , asyncio.TimeoutError) as e:
                        try:Members.append(randuser)
                        except:pass
                        self.ui.log_adder.appendPlainText(self.get_time()+"TimeoutError: "+str(e)+" - Account: "+phone)
                        break
                    except (IndexError , NameError):
                        self.ui.log_adder.appendPlainText(self.get_time()+"stop account Error (IndexError , NameError) - Account: "+phone)
                        break
                    except errors.UserChannelsTooMuch:
                        self.ui.log_adder.appendPlainText(self.get_time()+"The user ["+randuser+"] Channels too much joined! - Account: "+phone)
                        Badm += 1
                        BAD += 1
                    except errors.ChatInvalid:
                        try:Members.append(randuser)
                        except:pass
                        self.ui.log_adder.appendPlainText(self.get_time()+"The chat is invalid! - Account: "+phone)
                        break
                    except sqlite3.OperationalError:
                        try:Members.append(randuser)
                        except:pass
                        self.ui.log_adder.appendPlainText(self.get_time()+"database is locked! - Account: "+phone)
                        break
                    except errors.PeerFlood:
                        try:Members.append(randuser)
                        except:pass
                        self.ui.log_adder.appendPlainText(self.get_time()+"PEER FLOOD! - Account: "+phone)
                        break
                    except Exception as e:
                        traceback.print_exc()
                        if 'check @SpamBot for details' in str(e):
                            try:Members.append(randuser)
                            except:pass
                            self.ui.log_adder.appendPlainText(self.get_time()+"Account has Unfortunately (reported)! - Account: "+phone)
                            break
                        elif 'USERNAME_INVALID'in str(e) or "The username is invalid" in str(e):
                            self.ui.log_adder.appendPlainText(self.get_time()+"The username is invalid! - Account: "+phone)
                            Badm += 1
                            BAD += 1
                            error_count += 1
                        elif 'CHAT_MEMBER_ADD_FAILED'in str(e):
                            self.ui.log_adder.appendPlainText(self.get_time()+"CHAT MEMBER ADD FAILED! - Account: "+phone)
                            Badm += 1
                            BAD += 1
                            error_count += 1
                        elif 'The chat is invalid'in str(e):
                            try:Members.append(randuser)
                            except:pass
                            self.ui.log_adder.appendPlainText(self.get_time()+"The chat is invalid! - Account: "+phone)
                            break
                        else:
                            self.ui.log_adder.appendPlainText(self.get_time()+"Error: "+str(e)+" - Account: "+phone)
                            Badm += 1
                            BAD += 1
                            error_count += 1
                    await asyncio.sleep(random.randint(20,100))

                if phone in Runs:Runs.remove(phone)
                if phone not in Final:Final.append(phone)
                self.ui.log_adder.appendPlainText(self.get_time()+"Successful : {} Unsuccessful : {} - Account: {} => End adding!".format(OK,BAD,phone))
                try:await cli.disconnect()
                except:pass
            else:
                self.ui.log_adder.appendPlainText(self.get_time()+"Error join : {} - Account: {} => End adding!".format(chat[0],phone))
                try:await cli.disconnect()
                except:pass
                if phone in Runs:Runs.remove(phone)
                if phone not in Final:Final.append(phone)
        except Exception as e:
            traceback.print_exc()
            self.ui.log_adder.appendPlainText(self.get_time()+"Error: "+str(e)+" - Account: "+phone)
            try:await cli.disconnect()
            except:pass
            if phone in Runs:Runs.remove(phone)
            if phone not in Final:Final.append(phone)
        return False



                        

                        
                    

    @asyncSlot()
    async def start_adder(self):
        global Status , Members , Okm , Badm
        
        if Status:
            # QMessageBox.critical(self, "Error", "Adding is active.")
            await self.show_async_message("Error", "Adding is active.", icon=QMessageBox.Icon.Critical)
            return
        
        if Members == []:
            # QMessageBox.critical(self, "Error", "No members to add.")
            await self.show_async_message("Error", "No members to add.", icon=QMessageBox.Icon.Critical)
            return

        link = self.ui.input_link_add.text()
        if link.startswith("-100") and link.replace("-100","").isdigit():
            number_add , number_account = self.ui.number_add_bot.value() , self.ui.number_acc_add.value()
            if number_account > len(telegram_panel.list_accounts()) or number_account < 1:
                # QMessageBox.critical(self, "Error", "Not enough accounts.")
                await self.show_async_message("Error", "Not enough accounts.", icon=QMessageBox.Icon.Critical)
                return
            if number_add < 1:
                # QMessageBox.critical(self, "Error", "Number of members to add must be at least 1.")
                await self.show_async_message("Error", "Number of members to add must be at least 1.", icon=QMessageBox.Icon.Critical)
                return
            Status = True
            Okm , Badm = 0 , 0
            self.ui.log_adder.clear()
            self.ui.log_adder.setReadOnly(True)
            self.ui.input_link_add.setReadOnly(True)
            self.ui.number_add_bot.setReadOnly(True)
            self.ui.number_acc_add.setReadOnly(True)
            self.ui.log_adder.appendPlainText(self.get_time()+"Status: Active")
            self.ui.log_adder.appendPlainText(self.get_time()+"Link: {}".format(link))
            self.ui.log_adder.appendPlainText(self.get_time()+"Number of members to add: {}".format(number_add))
            self.ui.log_adder.appendPlainText(self.get_time()+"Number of accounts: {}".format(number_account))
            asyncio.create_task(self.run_adder())
            await self.show_async_message("Success", "Adding started.", icon=QMessageBox.Icon.Information)
            return
        else:
            # QMessageBox.critical(self, "Error", "Invalid link.")
            await self.show_async_message("Error", "Invalid ChatID.", icon=QMessageBox.Icon.Critical)
            return
        
    
    def save_log(self):
        log = self.ui.log_adder.toPlainText()
        if len(log) < 3:
            QMessageBox.critical(self, "Error", "Not text in log to save.")
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        name = f"{now}_Log.txt"
        with open(name,"w", encoding="utf-8") as f:
            f.write(log)
        QMessageBox.information(self, "Success", "save log to file => {}".format(name))
        return
    
    
    def get_time(self) -> str:
        return str(datetime.now().strftime("[%Y-%m-%d %H:%M:%S] "))
                
                
if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = MainWindow()
    window.show()
    with loop:
        loop.run_forever()
