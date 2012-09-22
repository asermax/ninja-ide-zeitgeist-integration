# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
#
# Copyright (C) 2012 - Agustín Carrasco
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.
import time
from os import path
from zeitgeist.client import ZeitgeistClient
from zeitgeist.datamodel import *

from ninja_ide.core import plugin


class ZeitgeistIntegration(plugin.Plugin):
    '''
    Plugin that enables integration with the Zeitgeist Framework.
    '''

    def initialize(self):
        '''
        Inicializes the Zeitgeist client and registers itself as a Zeitgeist
        data source.
        '''
        self.logger.info('Initialiazing zeitgeist plugin')
        editor = self.locator.get_service('editor')
        editor.fileOpened.connect(self._zeitgeist_log_file_open)
        editor.fileSaved.connect(self._zeitgeist_log_file_modified)

        #initialize zeitgeist client
        self.zeitgeist = ZeitgeistClient()
        self._register_data_source()

    def finish(self):
        '''
        Deletes the reference to the Zeitgeist client.
        '''
        # remove zeitgeist client
        del self.zeitgeist

        self.logger.info('Shutting down zeitgeist plugin')

    def _register_data_source(self):
        '''
        Registers the plugin as a Zeitgeist data source.
        '''
        unique_id = 'org.ninja.ide'
        name = 'Ninja IDE'
        description = 'Very versatile Python IDE'

        # Describe what sort of events will be inserted
        templates = []
        for interp in (Interpretation.EVENT_INTERPRETATION.ACCESS_EVENT,
            Interpretation.EVENT_INTERPRETATION.MODIFY_EVENT,
            Interpretation.EVENT_INTERPRETATION.LEAVE_EVENT,
            Interpretation.EVENT_INTERPRETATION.CREATE_EVENT):

            event_template = Event()
            event_template.interpretation = interp
            event_template.manifestation = Manifestation.USER_ACTIVITY

            for subj_interp in (Interpretation.DOCUMENT.TEXT_DOCUMENT.
                PLAIN_TEXT_DOCUMENT.SOURCE_CODE,
                Interpretation.DOCUMENT.TEXT_DOCUMENT.PLAIN_TEXT_DOCUMENT):

                subject_template = Subject()
                subject_template.interpretation = subj_interp
                subject_template.manifestation = Manifestation.FILE_DATA_OBJECT
                event_template.append_subject(subject_template)

            templates.append(event_template)

        self.zeitgeist.register_data_source(unique_id, name, description,
            templates)

    def _zeitgeist_log_event(self, fileName, interpretation):
        '''
        Registers an event over the file with a given interpretation.
        '''
        fileName = unicode(fileName)

        self.logger.info('Inserting event for %s' % fileName)

        subject = Subject.new_for_values(
            uri='file://%s' % fileName,
            origin='file://%s' % path.dirname(fileName),
            text=path.basename(fileName))
        event = Event.new_for_values(
            timestamp=int(time.time() * 1000),
            interpretation=interpretation,
            manifestation=Manifestation.USER_ACTIVITY,
            actor='application://ninja-ide.desktop',
            subjects=[subject])

        def on_id_received(event_ids):
            self.logger.info(
                'Logged %r with event id %d.' % (fileName, event_ids[0]))

        self.zeitgeist.insert_events([event], on_id_received)

    def _zeitgeist_log_file_open(self, fileName):
        '''
        Registers an event everytime Ninja IDE opens a file.
        '''
        self._zeitgeist_log_event(unicode(fileName),
            Interpretation.EVENT_INTERPRETATION.ACCESS_EVENT)

    def _zeitgeist_log_file_modified(self, fileName):
        '''
        Registers an event everytime Ninja IDE modifies a file.
        '''
        self._zeitgeist_log_event(unicode(fileName),
            Interpretation.EVENT_INTERPRETATION.MODIFY_EVENT)
