#! /usr/bin/python3

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import *

from xutil import *
import subprocess
import itertools
import functools
import math

def regular_divide(rect, cols, rows):
	dx = math.floor(float(rect.width()) / cols)
	dy = math.floor(float(rect.height()) / rows)

	grid = [
		[ QRect(rect.left() + dx * x, rect.top() + dy * y, dx, dy)
			for x in range(cols)] for y in range(rows)] 

	return grid

def create_rect(p0, p1):
	left = min(p0.x(), p1.x())
	right = max(p0.x(), p1.x())
	top = min(p0.y(), p1.y())
	bottom = max(p0.y(), p1.y())

	return QRect(left, top, right - left, bottom - top) 

def margin(m):
	return QMargins(m, m, m, m)

def bounding_rect(r0, r1):
	if (r0 is None):
		return r1
	if (r1 is None):
		return r0

	left = min(r0.left(), r1.left())
	right = max(r0.right(), r1.right())
	top = min(r0.top(), r1.top())
	bottom = max(r0.bottom(), r1.bottom())

	result = QRect(left, top, right - left, bottom - top)
	return result

QRect.asTuple = lambda self: (self.x(), self.y(), self.width(), self.height())

class DraggableGrid(QWidget):
	canceled = QtCore.pyqtSignal()
	selectRelease = QtCore.pyqtSignal([int, int, int, int])
	select = QtCore.pyqtSignal([int, int, int, int])

	def __init__(self, cols, rows, w=50, h=50):
		super(DraggableGrid, self).__init__()

		self.setMinimumSize(w, h)

		self.cols = cols
		self.rows = rows

		self.dragging = False
		self.dragStart = None
		self.draggable = True
		self.dragRectIndices = None
		self.manual_select = None

		self.content_margins = margin(8)
		self.cell_margins = margin(2)

		self.bg_color = QColor(60, 60, 60)
		self.fg_color = QColor(120, 120, 120)
		self.highlighted_color = QColor(220, 240, 230)
		self.nonhighlighted_color = QColor(160, 160, 160)

	def setSelected(self, rect):
		self.manual_select = rect
		self.select.emit(*rect.asTuple())
		self.repaint()

	def hasSelection(self):
		return (self.dragging or not (self.manual_select is None))

	def getSelection(self):
		if not self.manual_select is None:
			return self.manual_select
		elif self.dragging:
			return self.calculateSelectionRectFromDrag()
		else:
			return None

	def calculateSelectionRectFromDrag(self):
		return QRect(*self.calculateDragRectIndices())

	def emitAndClearSelection(self):
		if not (self.manual_select is None):
			old_select = self.manual_select
			self.manual_select = None
			self.selectRelease.emit(*old_select.asTuple())
			self.repaint()

	def clearSelection(self):
		self.manual_select = None
		self.repaint()

	def calculate_children(self):
		self.children = regular_divide(self.rect().marginsRemoved(self.content_margins), self.cols, self.rows)

	def is_selected(self, rect):
		return (self.dragging and self.dragRect.intersects(rect))

	def is_manual_selected(self, x, y):
		return (self.manual_select.adjusted(0,0,1,1).contains(QPoint(x, y)))
			
	def rect_active(self, x, y):
		if self.manual_select is None:
			return (self.is_selected(self.children[y][x]))
		else:
			return (self.is_manual_selected(x, y)
)
	def paintEvent(self, e):
		qp = QPainter()
		qp.begin(self)
		self.drawWidget(qp)
		qp.end()

	def drawWidget(self, qp):
		size = self.size()
		w = self.width()
		h = self.height()

		qp.setPen(self.bg_color)
		qp.setBrush(self.bg_color)
		qp.drawRect(0, 0, w, h)

		self.calculate_children()

		qp.setPen(self.fg_color)
		for x in range(self.cols):
			for y in range(self.rows):
				if (self.rect_active(x, y)):
					qp.setBrush(self.highlighted_color)
				else:
					qp.setBrush(self.nonhighlighted_color)
				qp.drawRect(self.children[y][x].marginsRemoved(self.cell_margins))
#				qp.drawRoundedRect(self.children[y][x].marginsRemoved(self.cell_margins), 3, 2)

	def calculateDragRectIndices(self):
		self.calculate_children()

		(min_x, max_x) = (self.cols, 0)
		(min_y, max_y) = (self.rows, 0)

		for x in range(self.cols):
			for y in range(self.rows):
				if (self.dragRect.intersects(self.children[y][x])):
					min_x = min(min_x, x)
					max_x = max(max_x, x)
					min_y = min(min_y, y)
					max_y = max(max_y, y)

		dragRectIndices = (min_x, min_y, max_x - min_x, max_y - min_y)
		return dragRectIndices

	def updateDragRectIndices(self):
		self.dragRectIndices = self.calculateDragRectIndices()

	def calculateDragRect(self):
		self.dragRect = create_rect(self.dragStart, self.dragEnd)

	def mouseMoveEvent(self, event):
		if (self.dragging and self.draggable):
			self.dragEnd = event.pos()
			self.calculateDragRect()
			newIndices = self.calculateDragRectIndices()
			if (newIndices != self.dragRectIndices):
				self.select.emit(*newIndices)
				self.dragRectIndices = newIndices

			self.repaint()

	def mousePressEvent(self, event):
		if (event.button() == Qt.RightButton):
			self.canceled.emit()
		elif (event.button() == Qt.LeftButton and self.draggable):
			self.dragging = True
			self.dragStart = event.pos()
			self.dragEnd = QPoint(event.pos().x() + 1, event.pos().y() + 1)
			self.calculateDragRect()
			newIndices = self.calculateDragRectIndices()
			if (newIndices != self.dragRectIndices):
				self.select.emit(*newIndices)
				self.dragRectIndices = newIndices
			self.repaint()
			
	def mouseReleaseEvent(self, event):
		if (event.button() == Qt.LeftButton and self.draggable):
			self.updateDragRectIndices()
			self.dragging = False
			self.selectRelease.emit(*self.dragRectIndices)
			self.repaint()

class ResizeFrame(QDialog):
	def __init__(self, parent=None):
		super(ResizeFrame, self).__init__(parent, Qt.Tool)

		self.border_width = 5
		self.setStyleSheet("""
			background-color: rgba(20, 20, 20, .5);
			border: 2px solid rgba(70, 70, 70, .5);
		""")

	def resizeEvent(self, event):
		self.setMask(QRegion(self.rect())
			.subtracted(QRegion(self.rect().marginsRemoved(margin(self.border_width)))))

class ResizerForm(QWidget):
	def __init__(self, window_id=None, parent=None):
		super(ResizerForm, self).__init__(parent, Qt.FramelessWindowHint | Qt.Dialog | Qt.Tool | Qt.Popup)

		self.setStyleSheet("""
			background-color: rgb(60, 60, 60);
		""")

		self.resizeFrame = ResizeFrame()

		self.cols = 6
		self.rows = 4

		grid_height = 1080 / 8
		grid_width = 1920 / 8

		formLayout = QGridLayout()
		formLayout.setContentsMargins(2,2,2,2)

		formLayout.setSpacing(0)

		left_drag = DraggableGrid(1, self.rows, 30, grid_height)
		left_drag.content_margins = margin(0)
		left_drag.cell_margins = margin(2)

		left_drag.nonhighlighted_color = QColor(100, 100, 100)
		left_drag.fg_color = QColor(100, 100, 100)
		left_drag.highlighted_color = QColor(160, 160, 160)

		left_drag.select.connect(self.select_rows)
		left_drag.canceled.connect(self.close)
		left_drag.selectRelease.connect(self.selected_rows)
		
		top_drag = DraggableGrid(self.cols, 1, grid_width, 30)
		top_drag.content_margins = margin(0)
		top_drag.cell_margins = margin(2)

		top_drag.nonhighlighted_color = QColor(100, 100, 100)
		top_drag.fg_color = QColor(100, 100, 100)
		top_drag.highlighted_color = QColor(160, 160, 160)

		top_drag.select.connect(self.select_cols)
		top_drag.canceled.connect(self.close)
		top_drag.selectRelease.connect(self.selected_cols)

		self.drag_grid = DraggableGrid(self.cols, self.rows, grid_width, grid_height)
		self.drag_grid.content_margins = margin(0)
		self.drag_grid.canceled.connect(self.close)
		self.drag_grid.selectRelease.connect(self.selected)
		self.drag_grid.select.connect(self.updatePreview)

		formLayout.addWidget(left_drag, 1, 0)
		formLayout.addWidget(top_drag, 0, 1)
		formLayout.addWidget(self.drag_grid, 1, 1)

		self.setLayout(formLayout)
		self.adjustSize()

		self.center()

	def keyPressEvent(self, e):
		self.updatePreview()

	def keyReleaseEvent(self, e):
		self.updatePreview()

	def updatePreview(self):
		if (self.drag_grid.hasSelection()):
			(x, y, w, h) = self.drag_grid.getSelection().asTuple()
			result_rect = self.calculate_screen_rect(x, y, w, h)
			self.resizeFrame.move(result_rect.topLeft())
			self.resizeFrame.resize(result_rect.size())
			self.resizeFrame.show()
			self.raise_()
			self.setFocus()
		else:
			self.resizeFrame.hide()

	def calculate_screen_rect(self, x, y, w, h):
		shift_key = QApplication.queryKeyboardModifiers() & Qt.ShiftModifier
		self.window_padding = 10 if shift_key else 0

		target_grid = QDesktopWidget().availableGeometry()

		grid = regular_divide(target_grid, self.cols, self.rows)

		result_rect = grid[y][x]
		for i in range(w + 1):
			for j in range(h + 1):
				result_rect = bounding_rect(result_rect, grid[y + j][x + i])

		result_rect = result_rect.marginsRemoved(margin(self.window_padding))

		return result_rect

	def selected(self, x, y, w, h):
		result_rect = self.calculate_screen_rect(x, y, w, h)
		self.updatePreview()

		for _ in range(3):
			window_move_resize(window_id, result_rect)

	def select_rows(self, x, y, w, h):
		self.drag_grid.setSelected(QRect(0, y, self.cols - 1, h))

	def selected_rows(self, x, y, w, h):
		self.drag_grid.setSelected(QRect(0, y, self.cols - 1, h))
		self.drag_grid.emitAndClearSelection()

	def select_cols(self, x, y, w, h):
		self.drag_grid.setSelected(QRect(x, 0, w, self.rows - 1))

	def selected_cols(self, x, y, w, h):
		self.drag_grid.setSelected(QRect(x, 0, w, self.rows - 1))
		self.drag_grid.emitAndClearSelection()

	def closeEvent(self, event):
		event.accept()
		QApplication.quit()

	def center(self):
		self.move(QCursor.pos() - self.frameGeometry().center())

if __name__ == '__main__':
	import sys
	from optparse import OptionParser

	usage = "usage: %prog [options] arg"
	parser = OptionParser(usage)
	parser.add_option("-w", "--window", dest="window_id",
                  help="Modify window with id ID", metavar="ID")

	(options, args) = parser.parse_args()

	if (not options.window_id):
		window_id = get_active_window()
	else:
		window_id = options.window_id

	app = QApplication(sys.argv)
 
	screen = ResizerForm(window_id)
	screen.show()
 
	sys.exit(app.exec_())
