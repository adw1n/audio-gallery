import time

from selenium.common.exceptions import NoSuchElementException

from audio_profiling import models
from .base import FunctionalTest


class CasualBrowsingTest(FunctionalTest):
    def test_data_setup_and_casual_browsing(self):
        self.mario = models.AudioPage.objects.create(name_en="Super Mario Bros", name_pl="Mario",
                                                     description_en="video game created by Nintendo")

        self.lvls = [models.Category.objects.create(name_en="level one", name_pl="poziom pierwszy"),
                     models.Category.objects.create(name_en="level two", name_pl="poziom drugi"),
                     models.Category.objects.create(name_en="level three", name_pl="poziom trzeci")]
        self.mario.categories.add(*self.lvls)

        demo_audio = models.AudioFile.objects.create(
            title="demo audio 1",
            category=self.lvls[0],
            audio_page=self.mario)
        demo_audio.audio_file.name = self.files[0]
        demo_audio.save()
        demo_audio.refresh_from_db()


        self.browser.get(self.live_server_url)
        time.sleep(2) # let the page load


        self.browser.find_element_by_xpath("//a[span[text()='Super Mario Bros']]").click() # TODO if selected then <b>
        self.assertRaises(NoSuchElementException, self.browser.find_element_by_link_text, "level two")
        self.assertRaises(NoSuchElementException, self.browser.find_element_by_link_text, "level three")
        lvl_one_link = self.browser.find_element_by_link_text("level one")
        lvl_one_link.click()


        self.check_page(demo_audio)


        # change the language
        pl_language = self.browser.find_element_by_link_text("PL")
        pl_language.click()
        time.sleep(2)
        self.check_page(demo_audio)
