from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.core.window import Window
from kivy.metrics import dp
import json
import os
from datetime import datetime

Window.size = (500, 700)

class BaseItem(BoxLayout):
    def __init__(self, item_type='note', text='', completed=False, item_id=0, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50)
        self.padding = [dp(10), dp(5)]
        self.spacing = dp(10)
        
        self.item_id = item_id
        self.item_type = item_type
        
        if item_type == 'note':
            self.checkbox = CheckBox(active=completed)
            self.checkbox.bind(active=self.on_checkbox_active)
            self.add_widget(self.checkbox)
        
        self.label = Label(text=text, size_hint_x=0.7, halign='left', valign='middle')
        self.label.text_size = (self.label.width, None)
        self.add_widget(self.label)
        
        delete_btn = Button(text='X', size_hint_x=0.1, background_color=(1, 0, 0, 1))
        delete_btn.bind(on_press=self.delete_item)
        self.add_widget(delete_btn)
    
    def on_checkbox_active(self, instance, value):
        app = App.get_running_app()
        app.update_item_status(self.item_type, self.item_id, value)
    
    def delete_item(self, instance):
        app = App.get_running_app()
        app.delete_item(self.item_type, self.item_id)

class SmartNotesPlusApp(App):
    def build(self):
        self.title = "Розумні нотатки +"
        self.data = {
            'notes': [],
            'contacts': [],
            'quotes': []
        }
        self.next_id = {
            'note': 1,
            'contact': 1,
            'quote': 1
        }
        self.load_data()
        
        self.tab_panel = TabbedPanel(do_default_tab=False)
        
        self.add_tab('Нотатки', 'note')
        self.add_tab('Контакти', 'contact')
        self.add_tab('Цитати', 'quote')
        
        return self.tab_panel
    
    def add_tab(self, tab_name, item_type):
        tab = TabbedPanelItem(text=tab_name)
        
        layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        input_field = TextInput(
            hint_text=f'Додати {tab_name.lower()}...',
            size_hint_y=None,
            height=dp(50),
            multiline=False
        )
        input_field.bind(on_text_validate=self.create_add_handler(item_type, input_field))
        layout.add_widget(input_field)
        
        add_btn = Button(
            text=f'Додати {tab_name.lower()}',
            size_hint_y=None,
            height=dp(50),
            background_color=(0, 0.7, 0, 1)
        )
        add_btn.bind(on_press=self.create_add_handler(item_type, input_field))
        layout.add_widget(add_btn)
        
        scroll_view = ScrollView()
        items_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        items_layout.bind(minimum_height=items_layout.setter('height'))
        scroll_view.add_widget(items_layout)
        layout.add_widget(scroll_view)
        
        setattr(self, f'{item_type}_layout', items_layout)
        setattr(self, f'{item_type}_input', input_field)
        
        tab.add_widget(layout)
        self.tab_panel.add_widget(tab)
        self.update_items_display(item_type)
    
    def create_add_handler(self, item_type, input_field):
        def handler(instance):
            self.add_item(item_type, input_field.text)
        return handler
    
    def add_item(self, item_type, text):
        text = text.strip()
        if text:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_item = {
                'id': self.next_id[item_type],
                'text': text,
                'created_at': timestamp,
                'updated_at': timestamp
            }
            
            if item_type == 'note':
                new_item['completed'] = False
            
            self.data[f'{item_type}s'].append(new_item)
            self.next_id[item_type] += 1
            self.save_data()
            self.update_items_display(item_type)
            getattr(self, f'{item_type}_input').text = ''
    
    def update_item_status(self, item_type, item_id, completed):
        for item in self.data[f'{item_type}s']:
            if item['id'] == item_id:
                item['completed'] = completed
                item['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break
        self.save_data()
        self.update_items_display(item_type)
    
    def delete_item(self, item_type, item_id):
        self.data[f'{item_type}s'] = [item for item in self.data[f'{item_type}s'] if item['id'] != item_id]
        self.save_data()
        self.update_items_display(item_type)
    
    def update_items_display(self, item_type):
        layout = getattr(self, f'{item_type}_layout')
        layout.clear_widgets()
        
        for item in self.data[f'{item_type}s']:
            item_widget = BaseItem(
                item_type=item_type,
                text=item['text'],
                completed=item.get('completed', False),
                item_id=item['id']
            )
            layout.add_widget(item_widget)
    
    def load_data(self):
        try:
            if os.path.exists('data.json'):
                with open('data.json', 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    self.data = loaded_data.get('data', {
                        'notes': [],
                        'contacts': [],
                        'quotes': []
                    })
                    for item_type in ['note', 'contact', 'quote']:
                        if self.data[f'{item_type}s']:
                            self.next_id[item_type] = max(item['id'] for item in self.data[f'{item_type}s']) + 1
                        else:
                            self.next_id[item_type] = 1
        except Exception as e:
            print(f"Помилка завантаження даних: {e}")
    
    def save_data(self):
        try:
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump({'data': self.data}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Помилка збереження даних: {e}")

if __name__ == '__main__':
    SmartNotesPlusApp().run() #Це ще не кінець, хочу ще багато чого додати
