import time

from selenium.common.exceptions import NoSuchElementException

from audio_profiling import models, tasks
from .base import FunctionalTest


class CasualBrowsingTest(FunctionalTest):
    def create_data(self):
        # audio page no. 1
        # game Super Mario Bros with a couple music files for each level in the game
        self.mario = models.AudioPage.objects.create(name_en="Super Mario Bros", name_pl="Mario Pl",
                                                     description_en="video game created by Nintendo")

        self.lvls = [models.Category.objects.create(name_en="level one", name_pl="poziom pierwszy"),
                     models.Category.objects.create(name_en="level two", name_pl="poziom drugi"),
                     models.Category.objects.create(name_en="level three", name_pl="poziom trzeci")]
        self.mario.categories.add(*self.lvls)

        self.lvl1_audio = models.AudioFile.objects.create(
            title="demo audio 1",
            category=self.lvls[0],
            audio_page=self.mario)
        self.lvl1_audio.audio_file.name = self.files[0]
        self.lvl1_audio.save()
        self.lvl1_audio.refresh_from_db()
        self.check_audio_file_tasks_completed(self.lvl1_audio)

        self.lvl3_audio = models.AudioFile.objects.create(
            title="demo audio lvl 3",
            category=self.lvls[2],
            audio_page=self.mario)
        self.lvl3_audio.audio_file.name = self.files[1]
        self.lvl3_audio.save()
        self.lvl3_audio.refresh_from_db()
        self.check_audio_file_tasks_completed(self.lvl1_audio)
        
        # audio page no. 2
        # game Guild Wars with a couple music files for different missions in the game
        self.guild_wars = models.AudioPage.objects.create(
            name_en="Guild Wars", name_pl="Wojny Gildii", description_en="MMORPG",
            description_pl="MMORPG stworzone przez ArenaNet")
        self.guild_wars.photo.name = tasks.get_media_path(self.photo)
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
        time.sleep(2)


        self.check_page(self.mario, self.lvl1_audio, "en")


        pl_language = self.browser.find_element_by_link_text("PL")
        pl_language.click()
        time.sleep(2)
        self.check_page(self.mario, self.lvl1_audio, "pl")



        lvl_three_link = self.browser.find_element_by_link_text(self.lvls[2].name_pl)
        lvl_three_link.click()
        time.sleep(2)
        self.check_page(self.mario, self.lvl3_audio, "pl")

        self.browser.find_element_by_link_text("EN").click()
        time.sleep(2)

        # test the other audio page - different game
        self.browser.find_element_by_xpath("//a[span[text()='%s']]" % self.guild_wars.name_en).click()
        time.sleep(0.5)
        self.browser.find_element_by_link_text(self.elite_missions_themes.name_en).click()
        self.browser.find_element_by_link_text(self.fow_theme.name_en).click()
        time.sleep(2)

        # test that the subcategory menu is opened and and current page is marked as active
        self.browser.find_element_by_link_text(self.fow_theme.name_en)
        self.assertIsNotNone(self.browser.execute_script('return $(\'li:has(a:contains(FOW theme))[class="active"]\')'))


        self.check_page(self.guild_wars, self.fow_audio, "en")


        # check that the spectrum is being calculated correctly
        ACCEPTABLE_SPECTRUM_READING_INACCURACY = 5
        self.set_audio_position(0)
        self.play_audio()  # let the spectrum refresh
        time.sleep(3)
        self.pause_audio()
        # check frequencies that are silenced at the moment
        self.assertAlmostEqual(self.get_spectrum_Db_value(5000), -100, ACCEPTABLE_SPECTRUM_READING_INACCURACY)
        self.assertAlmostEqual(self.get_spectrum_Db_value(15000), -100, ACCEPTABLE_SPECTRUM_READING_INACCURACY)
        # check the exact frequency that is being played and values near it
        self.assertGreater(self.get_spectrum_Db_value(10**4), -40)
        self.assertGreater(self.get_spectrum_Db_value(9990), -50)

        # test spectrum when there is silence
        self.set_audio_position(10)
        self.play_audio()
        time.sleep(2)
        self.pause_audio()
        self.assertAlmostEqual(self.get_spectrum_Db_value(5 * 10 ** 3), -100, ACCEPTABLE_SPECTRUM_READING_INACCURACY)
        self.assertAlmostEqual(self.get_spectrum_Db_value(10 ** 4), -100, ACCEPTABLE_SPECTRUM_READING_INACCURACY)
        self.assertAlmostEqual(self.get_spectrum_Db_value(15 * 10 ** 3), -100, ACCEPTABLE_SPECTRUM_READING_INACCURACY)


        # check that spectrum for the whole file is shown
        self.set_audio_position(0)
        # check the precise component frequencies values
        self.assertGreater(self.get_spectrum_Db_value(10000), -30)
        self.assertGreater(self.get_spectrum_Db_value(8000), -30)
        self.assertGreater(self.get_spectrum_Db_value(6000), -30)
        self.assertGreater(self.get_spectrum_Db_value(4000), -30)
        # check values in-between
        self.assertGreater(self.get_spectrum_Db_value(5000), -80)
        self.assertGreater(self.get_spectrum_Db_value(7000), -80)
        # check values that have nothing to do with component frequencies
        self.assertLess(self.get_spectrum_Db_value(15000), -90)
        self.assertLess(self.get_spectrum_Db_value(20000), -90)


        # set the start page and check that when the user hits the main page, the start page is returned correctly
        self.lvl3_audio.start_page = True
        self.lvl3_audio.save()
        self.browser.get(self.live_server_url)
        time.sleep(2)
        self.check_page(self.mario, self.lvl3_audio, "en")
