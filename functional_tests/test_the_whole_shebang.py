import time

from selenium.common.exceptions import NoSuchElementException

from audio_profiling import models, tasks
from .base import FunctionalTest


class CasualBrowsingTest(FunctionalTest):
    def test_data_setup_and_casual_browsing(self):
        self.mario = models.AudioPage.objects.create(name_en="Super Mario Bros", name_pl="Mario Pl",
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
        self.assertIsNotNone(demo_audio.waveform)
        self.assertIsNotNone(demo_audio.mp3)
        self.assertIsNotNone(demo_audio.spectrum)
        self.assertIsNotNone(demo_audio.spectrogram)
        self.assertIsNotNone(demo_audio.LEFT_IMG_MARGIN)
        self.assertIsNotNone(demo_audio.RIGHT_IMG_MARGIN)
        self.assertIsNotNone(demo_audio.TOP_IMG_MARGIN)
        self.assertIsNotNone(demo_audio.BOTTOM_IMG_MARGIN)


        self.browser.get(self.live_server_url)
        time.sleep(2) # let the page load


        self.browser.find_element_by_xpath("//a[span[text()='Super Mario Bros']]").click() # TODO if selected then <b>
        self.assertRaises(NoSuchElementException, self.browser.find_element_by_link_text, "level two")
        self.assertRaises(NoSuchElementException, self.browser.find_element_by_link_text, "level three")
        lvl_one_link = self.browser.find_element_by_link_text("level one")
        lvl_one_link.click()


        self.check_page(self.mario, demo_audio, "en")


        pl_language = self.browser.find_element_by_link_text("PL")
        pl_language.click()
        time.sleep(2)
        self.check_page(self.mario, demo_audio, "pl")




        # TODO add photo
        # TODO generate audio file with pauses and check spectrum when pause, and also check when music is being played
        # TODO test other categories
        # TODO test subcategory
        # TODO test other audiopage
        # TODO set start page and test if start page is returned
