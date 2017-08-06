import time

from selenium.common.exceptions import NoSuchElementException

from audio_profiling import models, tasks
from .base import FunctionalTest


class CasualBrowsingTest(FunctionalTest):
    def create_data(self):
        self.mario = models.AudioPage.objects.create(name_en="Super Mario Bros", name_pl="Mario Pl",
                                                     description_en="video game created by Nintendo")

        self.lvls = [models.Category.objects.create(name_en="level one", name_pl="poziom pierwszy"),
                     models.Category.objects.create(name_en="level two", name_pl="poziom drugi"),
                     models.Category.objects.create(name_en="level three", name_pl="poziom trzeci")]
        self.mario.categories.add(*self.lvls)

        self.demo_audio_lvl1 = models.AudioFile.objects.create(
            title="demo audio 1",
            category=self.lvls[0],
            audio_page=self.mario)
        self.demo_audio_lvl1.audio_file.name = self.files[0]
        self.demo_audio_lvl1.save()
        self.demo_audio_lvl1.refresh_from_db()
        self.check_audio_file_tasks_completed(self.demo_audio_lvl1)

        self.demo_audio_lvl3 = models.AudioFile.objects.create(
            title="demo audio lvl 3",
            category=self.lvls[2],
            audio_page=self.mario)
        self.demo_audio_lvl3.audio_file.name = self.files[1]
        self.demo_audio_lvl3.save()
        self.demo_audio_lvl3.refresh_from_db()
        self.check_audio_file_tasks_completed(self.demo_audio_lvl1)
        
        
        
        
        
        
        
        
        self.guild_wars = models.AudioPage.objects.create(
            name_en="Guild Wars", name_pl="Wojny Gildii", description_en="MMORPG",
            description_pl="MMORPG stworzone przez ArenaNet")
        self.guild_wars.photo.name = tasks.get_media_path(self.photo) # TODO in constructor
        self.guild_wars.save()
        self.guild_wars.refresh_from_db()

        self.elite_missions_themes = models.Category.objects.create(name_en="Elite missions")
        self.ugroz_theme = models.Category.objects.create(
            name_en="Ugroz theme",
            parent_category= self.elite_missions_themes)
        self.fow_theme = models.Category.objects.create(
            name_en="FOW theme",
            parent_category= self.elite_missions_themes)
        self.guild_wars.categories.add(self.elite_missions_themes)
        self.guild_wars.categories.add(self.ugroz_theme)
        self.guild_wars.categories.add(self.fow_theme)

        self.urgroz_audio = models.AudioFile.objects.create(
            title="urgroz theme audio",
            category=self.ugroz_theme,
            audio_page=self.guild_wars)
        self.urgroz_audio.audio_file.name = self.files[2]
        self.urgroz_audio.save()
        self.urgroz_audio.refresh_from_db()
        self.check_audio_file_tasks_completed(self.urgroz_audio)
        
        self.fow_audio = models.AudioFile.objects.create(
            title="fow theme audio",
            category=self.fow_theme,
            audio_page=self.guild_wars)
        self.fow_audio.audio_file.name = self.files[3]
        self.fow_audio.save()
        self.fow_audio.refresh_from_db()
        self.check_audio_file_tasks_completed(self.fow_audio)
    def test_data_setup_and_casual_browsing(self):
        # admin creates objects using the /admin page
        self.create_data()


        # a visitor goes to the web page
        self.browser.get(self.live_server_url)
        time.sleep(2) # let the page load

        # test the menus on the sidebar
        self.browser.find_element_by_xpath("//a[span[text()='Super Mario Bros']]").click()
        time.sleep(0.5)
        self.assertRaises(NoSuchElementException, self.browser.find_element_by_link_text, self.lvls[1].name_en)
        self.browser.find_element_by_link_text(self.lvls[2].name_en)
        lvl_one_link = self.browser.find_element_by_link_text(self.lvls[0].name_en)
        lvl_one_link.click()


        self.check_page(self.mario, self.demo_audio_lvl1, "en")


        pl_language = self.browser.find_element_by_link_text("PL")
        pl_language.click()
        time.sleep(2)
        self.check_page(self.mario, self.demo_audio_lvl1, "pl")



        lvl_three_link = self.browser.find_element_by_link_text(self.lvls[2].name_pl)
        lvl_three_link.click()
        time.sleep(2)
        self.check_page(self.mario, self.demo_audio_lvl3, "pl")

        self.browser.find_element_by_link_text("EN").click()

        # test the other audio page - different game
        self.browser.find_element_by_xpath("//a[span[text()='%s']]" % self.guild_wars.name_en).click()
        time.sleep(0.5)
        self.browser.find_element_by_link_text(self.elite_missions_themes.name_en).click()
        self.browser.find_element_by_link_text(self.fow_theme.name_en).click()
        self.check_page(self.guild_wars, self.fow_audio, "en")


        # set the start page and check that when user hits the main page, the start page is returned correctly
        self.demo_audio_lvl3.start_page = True
        self.demo_audio_lvl3.save()
        self.browser.get(self.live_server_url)
        time.sleep(2)
        self.check_page(self.mario, self.demo_audio_lvl3, "en")
