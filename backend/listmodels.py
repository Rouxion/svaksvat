import datetime

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ui.membershipedit import Ui_MembershipEdit

class MembershipListModel(QAbstractListModel):
    def __init__(self, session, member, parent=None):
        super().__init__(parent)
        self.session = session
        self.member = session.merge(member) # Get local object for this Model
        self._data = self.member.groupmemberships

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < self.rowCount():
            return None

        row = index.row()

        membership = self._data[row]
        duration = self.membershipDuration(membership)
        if role == Qt.DisplayRole:
            membership = self.data[row]
            duration = self.membershipDuration(membership)
            return "%s %s" % (membership.group.name_fld,
                    duration)

        elif role == Qt.EditRole:
            return membership

        return None

    def membershipDuration(self, membership):
        startyear = membership.startTime_fld.year
        endyear = membership.endTime_fld.year
        if startyear == endyear:
            return startyear
        startmonth = membership.startTime_fld.month
        endmonth = membership.endTime_fld.month
        return "%d.%d - %d.%d" % (startmonth, startyear, endmonth, endyear)

class MembershipDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QDialog(parent=parent)
        editor.setModal(True)
        editor.ui = Ui_MembershipEdit()
        editor.ui.setupUi(editor)

        editor.ui.startYear_spinBox.setRange(datetime.MINYEAR, datetime.MAXYEAR)

        # Connect signals to slots.
        editor.ui.buttonBox.accepted.connect(lambda:
                (self.commitData.emit(editor),self.closeEditor.emit(editor,
                    QAbstractItemDelegate.NoHint)))
        editor.ui.buttonBox.rejected.connect(
                lambda: self.closeEditor.emit(editor,
                    QAbstractItemDelegate.NoHint))
        editor.ui.wholeyear_radioButton.toggled.connect(editor.ui.startYearWidget.setVisible)
        editor.ui.laborday_radioButton.toggled.connect(editor.ui.startYearWidget.setVisible)
        editor.ui.otherMandate_radioButton.toggled.connect(editor.ui.startAndEndTimeWidget.setVisible)

        return editor

    def setEditorData(self, editor, index):
        membership = index.data(Qt.EditRole)
        startdate = membership.startTime_fld.date()
        enddate = membership.endTime_fld.date()

        editor.ui.startYear_spinBox.setFocus()

        # Whole year mandate
        if (startdate.year == enddate.year and
                startdate == datetime.date(startdate.year, 1, 1) and
                enddate == datetime.date(startdate.year, 12, 31)):
            editor.ui.wholeyear_radioButton.toggle()
            editor.ui.startAndEndTimeWidget.hide()

        # Labor day to labor day mandate
        elif (startdate.year == (enddate.year - 1) and
                startdate == datetime.date(startdate.year, 5, 1) and
                enddate == datetime.date(startdate.year + 1, 4, 30)):
            editor.ui.laborday_radioButton.toggle()
            editor.ui.startAndEndTimeWidget.hide()

        # Other mandate
        else:
            editor.ui.otherMandate_radioButton.toggle()
            editor.ui.startYearWidget.hide()

        editor.ui.startYear_spinBox.setValue(membership.startTime_fld.year)
        editor.ui.startTime_fld.setDate(membership.startTime_fld)
        editor.ui.endTime_fld.setDate(membership.endTime_fld)

    def setModelData(self, editor, model, index):
        startyear = editor.ui.startYear_spinBox.value()

        starttime = None
        endtime = None

        if editor.ui.otherMandate_radioButton.isChecked():
            starttime = editor.ui.startTime_fld.dateTime().toPyDateTime()
            endtime = editor.ui.endTime_fld.dateTime().toPyDateTime()
            if endtime < starttime:
                endtime = starttime # Don't allow endtime before starttime

        elif editor.ui.laborday_radioButton.isChecked():
            starttime = datetime.datetime(startyear, 5, 1)
            endtime = datetime.datetime(startyear + 1, 4, 30)

        elif editor.ui.wholeyear_radioButton.isChecked():
            starttime = datetime.datetime(startyear, 1, 1)
            endtime = datetime.datetime(startyear, 12, 31)

        else: assert()

        model.setData(index, (starttime, endtime), Qt.EditRole)

    def eventFilter(self, editor, event):
        if event.type() == QEvent.KeyPress:
            # Undo Tab-key override in QStyledItemDelegate
            # pressing tab would otherwise close the editor.
            if event.key() == Qt.Key_Tab:
                return False
        if event.type() == QEvent.FocusOut:
            # Don't close editor when it looses focus.
            return False
        return super().eventFilter(editor, event)
