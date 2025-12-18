import pygame as pg
from src.utils import load_sound, GameSettings

class SoundManager:
    def __init__(self):
        pg.mixer.init()
        pg.mixer.set_num_channels(GameSettings.MAX_CHANNELS)
        self.current_bgm = None
        self.muted = False
        
    def play_bgm(self, filepath: str):
        if self.current_bgm:
            self.current_bgm.stop()
        audio = load_sound(filepath)
        volume = 0.0 if self.muted else GameSettings.AUDIO_VOLUME
        audio.set_volume(volume)
        audio.play(-1)
        self.current_bgm = audio
        
    def pause_all(self):
        pg.mixer.pause()

    def resume_all(self):
        pg.mixer.unpause()
        
    def play_sound(self, filepath, volume=0.7):
        sound = load_sound(filepath)
        sound.set_volume(volume)
        sound.play()

    def stop_all_sounds(self):
        pg.mixer.stop()
        self.current_bgm = None
    
    def set_volume(self, volume: float):
        """Set the volume for all audio."""
        GameSettings.AUDIO_VOLUME = max(0.0, min(1.0, volume))
        if self.current_bgm:
            actual_volume = 0.0 if self.muted else GameSettings.AUDIO_VOLUME
            self.current_bgm.set_volume(actual_volume)
    
    def set_muted(self, muted: bool):
        """Set the mute state."""
        self.muted = muted
        if self.current_bgm:
            actual_volume = 0.0 if muted else GameSettings.AUDIO_VOLUME
            self.current_bgm.set_volume(actual_volume)
        if muted:
            self.pause_all()
        else:
            self.resume_all()