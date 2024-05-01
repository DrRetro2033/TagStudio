import logging

from PySide6.QtCore import Qt, QSize, QTimer, QVariantAnimation, QUrl, QObject, QEvent
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QResizeEvent
from PySide6.QtSvgWidgets import QSvgWidget

class VideoPlayer(QGraphicsView):
	"""A simple video player for the TagStudio application."""
	resolution = QSize(1280, 720)
	hover_fix_timer = QTimer()
	video_preview = None
	play_pause = None 
	mute_button = None 
	content_visible = False
	filepath = None

	def __init__(self) -> None:
		# Set up the base class.
		super().__init__()
		
		self.animation = QVariantAnimation(self)
		self.animation.valueChanged.connect(lambda value: self.set_tint_transparency(value))
		
		self.hover_fix_timer.timeout.connect(lambda: self.checkIfStillHovered())
		self.hover_fix_timer.setSingleShot(True)

		# Set up the video player.	
		self.installEventFilter(self)
		self.setMouseTracking(True)
		self.setScene(QGraphicsScene(self))
		self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
		self.player = QMediaPlayer(self)
		self.player.mediaStatusChanged.connect(lambda: self.check_media_status(self.player.mediaStatus()))
		self.video_preview = QGraphicsVideoItem()
		self.player.setVideoOutput(self.video_preview)
		self.video_preview.setAcceptHoverEvents(True)
		self.video_preview.installEventFilter(self)
		self.player.setAudioOutput(QAudioOutput(QMediaDevices().defaultAudioOutput(),self.player))
		self.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.scene().addItem(self.video_preview)
		self.setMouseTracking(True)

		# Set up the video tint.
		self.video_tint = self.scene().addRect(0, 0, self.video_preview.size().width(), self.video_preview.size().height(), QPen(QColor(0, 0, 0, 0)), QBrush(QColor(0, 0, 0, 0)))
		# self.video_tint.setParentItem(self.video_preview)

		# Set up the buttons.
		self.play_pause = QSvgWidget('./tagstudio/resources/pause.svg', self)
		self.play_pause.setMouseTracking(True)
		self.play_pause.installEventFilter(self)
		self.scene().addWidget(self.play_pause)
		self.play_pause.resize(100, 100)
		self.play_pause.move(self.width()/2 - self.play_pause.size().width()/2, self.height()/2 - self.play_pause.size().height()/2)
		self.play_pause.hide()

		self.mute_button = QSvgWidget('./tagstudio/resources/volume_muted.svg', self)
		self.mute_button.setMouseTracking(True)
		self.mute_button.installEventFilter(self)
		self.scene().addWidget(self.mute_button)
		self.mute_button.resize(40, 40)
		self.mute_button.move(self.width() - self.mute_button.size().width()/2, self.height() - self.mute_button.size().height()/2)
		self.mute_button.hide()

	def check_media_status(self, media_status:QMediaPlayer.MediaStatus) -> None:
		logging.info(media_status)
		if media_status == QMediaPlayer.MediaStatus.EndOfMedia:
			#Switches current video to with video at filepath. Reason for this is because Pyside6 is dumb and can't handle setting a new source and freezes.
			#Even if I stop the player before switching, it breaks.
			#On the plus side, this adds infinite looping for the video preview.
			self.player.setSource(QUrl().fromLocalFile(self.filepath))
			logging.info(f'Set source to {self.filepath}.')
			# self.video_preview.setSize(self.resolution)
			
			self.player.setPosition(0)
			logging.info(f'Set muted to true.')
			self.player.play()
			logging.info(f'Successfully played.')
			self.keep_controls_in_place()
			self.update_controls()
	def update_controls(self) -> None:
		if self.player.audioOutput().isMuted():
			self.mute_button.load('./tagstudio/resources/volume_muted.svg')
		else:
			self.mute_button.load('./tagstudio/resources/volume_unmuted.svg')

		if self.player.isPlaying():
			self.play_pause.load('./tagstudio/resources/pause.svg')
		else:
			self.play_pause.load('./tagstudio/resources/play.svg')
	def eventFilter(self, obj:QObject, event:QEvent) -> bool:
		#This chunk of code is for the video controls.
		if obj == self.play_pause and event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
			if self.player.hasVideo():
				self.pause_toggle()
		
		if obj == self.mute_button and event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
			if self.player.hasAudio():
				self.mute_toggle()

		if obj == self.video_preview and event.type() == QEvent.Type.GraphicsSceneHoverEnter or event.type() == QEvent.Type.HoverEnter:
			if self.video_preview.isUnderMouse():
				self.underMouse()
				self.hover_fix_timer.start(10)
		elif obj == self.video_preview and event.type() == QEvent.Type.GraphicsSceneHoverLeave or event.type() == QEvent.Type.HoverLeave:
			if not self.video_preview.isUnderMouse():
				self.hover_fix_timer.stop()
				self.releaseMouse()


		return super().eventFilter(obj, event)
	
	def check_if_still_hovered(self) -> None:
		#Yet again, Pyside6 is dumb. I don't know why, but the HoverLeave event is not triggered sometimes and does not hide the controls.
		#So, this is a workaround. This is called by a QTimer every 10ms to check if the mouse is still in the video preview.
		if not self.video_preview.isUnderMouse():
			self.releaseMouse()
		else:
			self.hover_fix_timer.start(10)
	
	def set_tint_transparency(self, value) -> None:
		self.video_tint.setBrush(QBrush(QColor(0, 0, 0, value)))

	def underMouse(self) -> bool:
		logging.info('under mouse')
		self.animation.setStartValue(self.video_tint.brush().color().alpha())
		self.animation.setEndValue(100)
		self.animation.setDuration(500)
		self.animation.start()
		self.play_pause.show()
		self.mute_button.show()
		self.keep_controls_in_place()
		return super().underMouse()

	def releaseMouse(self) -> None:
		logging.info('release mouse')
		self.animation.setStartValue(self.video_tint.brush().color().alpha())
		self.animation.setEndValue(0)
		self.animation.setDuration(500)
		self.animation.start()
		self.play_pause.hide()
		self.mute_button.hide()
		return super().releaseMouse()
	
	def reset_controls_to_default(self) -> None:
		# Resets the video controls to their default state.
		self.play_pause.load('./tagstudio/resources/pause.svg')
		self.mute_button.load('./tagstudio/resources/volume_muted.svg')


	def pause_toggle(self) -> None:
		if self.player.isPlaying():
			self.player.pause()
			self.play_pause.load('./tagstudio/resources/play.svg')
		else:
			self.player.play()
			self.play_pause.load('./tagstudio/resources/pause.svg')
	
	def mute_toggle(self) -> None:
		if self.player.audioOutput().isMuted():
			self.player.audioOutput().setMuted(False)
			self.mute_button.load('./tagstudio/resources/volume_unmuted.svg')
		else:
			self.player.audioOutput().setMuted(True)
			self.mute_button.load('./tagstudio/resources/volume_muted.svg')

	def play(self, filepath: str, resolution: QSize) -> None:
		# Sets the filepath and sends the current player position to the very end, so that the new video can be played.
		self.player.audioOutput().setMuted(True)
		logging.info(f'Playing {filepath}')
		self.resolution = resolution
		self.filepath = filepath
		if self.player.isPlaying():
			self.player.setPosition(self.player.duration())
			self.player.play()
		else:
			self.check_media_status(QMediaPlayer.MediaStatus.EndOfMedia)

		logging.info(f'Successfully stopped.')

	def stop(self) -> None:
		# Stops the video.
		self.player.stop()

	def resize_video(self, new_size : QSize,) -> None:
		# Resizes the video preview to the new size.
		self.video_preview.setSize(new_size)
		self.video_tint.setRect(0, 0, self.video_preview.size().width(), self.video_preview.size().height())
		self.centerOn(self.video_preview)
		self.keep_controls_in_place()

	def keep_controls_in_place(self) -> None:
		# Keeps the video controls in the places they should be.
		self.play_pause.move(self.width()/2 - self.play_pause.size().width()/2, self.height()/2 - self.play_pause.size().height()/2)
		self.mute_button.move(self.width() - self.mute_button.size().width()-10, self.height() - self.mute_button.size().height()-10)

	def resizeEvent(self, event: QResizeEvent) -> None:
		# Keeps the video preview in the center of the screen.
		self.centerOn(self.video_preview)
		return
		# return super().resizeEvent(event)