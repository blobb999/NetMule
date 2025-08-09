#### Offene Tasks ####
#Sprachunterstützung englisch/deutsch - Begriffe sollten flexibel aus externer definition importierbar und ebensol flexibel auf weitere Sprachen erweiterbar sein.
#Bildausrichtung pulldown: links, rechts, füllend (Bild wird dynamisch in Knotengrösse eingepasst, für links rechts ist die definierte Höhe des Knotens Referenz des Massstab)
#Geburtsdatum: Checkbox für zeigen - pulldownmenu: links, mitte, rechts
#Notizen: Checkbox für zeigen - pulldown: links, mitte, rechts
#Mousover: Zeige alle Informationen bei Mouseover

import sys
import json
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QGraphicsScene, QGraphicsView, QMenu,
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPolygonItem, QGraphicsTextItem,
    QGraphicsLineItem, QColorDialog, QFontDialog, QInputDialog, QFileDialog,
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QComboBox, QMessageBox
)
from PyQt5.QtGui import QBrush, QPen, QColor, QFont, QPainter, QPixmap, QImage, QPolygonF
from PyQt5.QtCore import Qt, QPointF, QRectF
import networkx as nx
from python_gedcom_2.parser import Parser
from language_manager import get_language_manager, tr

DEFAULT_SIZE = 40  # Standardgröße für Knoten (Höhe/Breite für Rechtecke)

class NodeItem(QGraphicsRectItem):
    def __init__(self, name, birth="", notes="", photo=None, pos=QPointF(0, 0), graph=None, scene=None, shape="rectangle", size=DEFAULT_SIZE, parent=None, color=None, font_family="Arial", font_size=10, font_weight=QFont.Normal, font_italic=False):
        super().__init__(-size, -size/2, size*2, size, parent)
        self.setFlags(self.ItemIsMovable | self.ItemIsSelectable | self.ItemSendsGeometryChanges)
        self.name = name
        self.birth = birth
        self.notes = notes
        self.photo = photo
        self.graph = graph
        self.scene_ref = scene
        self.edges = []
        self.shape = shape
        self.size = size
        self.color = QColor(color if color else "white")
        self.setPen(QPen(Qt.black))
        self.text = QGraphicsTextItem(name, self)
        self.font = QFont(font_family, font_size, font_weight)
        self.font.setItalic(font_italic)
        self.text.setFont(self.font)
        self.setPos(pos)
        
        # Farbe anwenden, wenn kein Foto vorhanden ist
        if not photo:
            self.setBrush(QBrush(self.color))
        
        # Debugging-Ausgabe
        print(f"NodeItem.__init__: Name={name}, Color={self.color.name()}, Font={font_family}, Size={font_size}, Weight={font_weight}, Italic={font_italic}")
        
        # Zum Graph hinzufügen
        if graph is not None:
            graph.add_node(
                name,
                birth=birth,
                notes=notes,
                photo=photo,
                color=self.color.name(),
                font_family=font_family,  # Schriftfamilie speichern
                font_size=font_size,
                font_weight=font_weight,  # Schriftgewicht speichern
                font_italic=font_italic,  # Kursiv speichern
                shape=shape,
                size=size,
                pos=[pos.x(), pos.y()]
            )
        
        if photo:
            self.load_photo(photo)
        self.update_shape()

    def update_shape(self):
        self.prepareGeometryChange()
        
        if self.shape == "rectangle":
            # Rechteck
            self.setRect(-self.size, -self.size/2, self.size*2, self.size)
        elif self.shape == "ellipse":
            # Ellipse
            self.setRect(QRectF(-self.size, -self.size/2, self.size*2, self.size))
        elif self.shape == "triangle":
            # Dreieck
            self.setRect(-self.size, -self.size/2, self.size*2, self.size)
        elif self.shape == "oval":
            # Oval - längeres, abgerundetes Rechteck
            self.setRect(QRectF(-self.size*1.5, -self.size/2, self.size*3, self.size))
        elif self.shape == "circle":
            # Kreis - quadratisches Rechteck für perfekten Kreis
            self.setRect(QRectF(-self.size, -self.size, self.size*2, self.size*2))
        
        # Text zentrieren
        self.text.setPos(-self.text.boundingRect().width()/2, -self.size/4)
        
        # Foto neu laden falls vorhanden
        if self.photo:
            self.load_photo(self.photo)

    def paint(self, painter, option, widget):
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        
        if self.shape == "rectangle":
            # Normale Rechtecke
            painter.drawRect(self.rect())
        elif self.shape == "ellipse":
            # Ellipse
            painter.drawEllipse(self.rect())
        elif self.shape == "triangle":
            # Dreieck
            polygon = QPolygonF([
                QPointF(0, -self.size/2),
                QPointF(-self.size, self.size/2),
                QPointF(self.size, self.size/2)
            ])
            painter.drawPolygon(polygon)
        elif self.shape == "oval":
            # Oval - abgerundetes Rechteck mit gleichmäßigen Radien
            painter.drawRoundedRect(self.rect(), self.size/2, self.size/2)
        elif self.shape == "circle":
            # Kreis - perfekte Ellipse mit gleicher Breite und Höhe
            painter.drawEllipse(self.rect())

    def load_photo(self, photo_path):
        try:
            image = QImage(photo_path)
            if not image.isNull():
                # Skalierung an die tatsächliche Rechteckgröße anpassen
                rect = self.rect()
                pixmap = QPixmap.fromImage(image.scaled(int(rect.width()), int(rect.height()), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.setBrush(QBrush(pixmap))
                print(f"NodeItem.load_photo: Name={self.name}, Photo={photo_path}, Color preserved={self.color.name()}")
            else:
                # Wenn das Foto ungültig ist, Farbe wiederherstellen
                self.setBrush(QBrush(self.color))
                print(f"NodeItem.load_photo: Name={self.name}, Invalid photo, restored Color={self.color.name()}")
        except Exception as e:
            print(f"NodeItem.load_photo: Error loading photo for {self.name}: {e}, restoring Color={self.color.name()}")
            self.setBrush(QBrush(self.color))

    def contextMenuEvent(self, event):
        menu = QMenu()
        add_child = menu.addAction(tr("context_menu.add_child"))
        add_partner = menu.addAction(tr("context_menu.add_partner"))
        connect = menu.addAction(tr("context_menu.connect"))
        add_existing_as_child = menu.addAction(tr("context_menu.add_existing_as_child"))
        edit = menu.addAction(tr("context_menu.edit"))
        resize = menu.addAction(tr("context_menu.resize"))
        delete = menu.addAction(tr("context_menu.delete"))
        
        action = menu.exec_(event.screenPos())
        
        if action == add_child:
            self.add_child()
        elif action == add_partner:
            self.add_partner()
        elif action == connect:
            if self.scene_ref:
                self.scene_ref.start_connection(self)
        elif action == add_existing_as_child:
            self.add_existing_node_as_child()
        elif action == edit:
            self.edit_node()
        elif action == resize:
            self.resize_node()
        elif action == delete:
            self.delete_node()

    def add_existing_node_as_child(self):
        """Fügt einen bereits existierenden Knoten als Kind hinzu"""
        if not self.scene_ref:
            return
        
        # Alle verfügbaren Knoten sammeln (außer sich selbst)
        available_nodes = []
        for item in self.scene_ref.items():
            if (isinstance(item, NodeItem) and 
                item != self and 
                item.name != self.name):
                available_nodes.append(item)
        
        if not available_nodes:
            QMessageBox.information(None, tr("messages.info"), 
                                  tr("messages.no_nodes_available"))
            return
        
        # Dialog zur Auswahl des Knotens
        node_names = [node.name for node in available_nodes]
        selected_name, ok = QInputDialog.getItem(
            None, 
            tr("dialogs.add_existing_node_as_child"),
            tr("dialogs.select_child_node"),
            node_names,
            0,
            False
        )
        
        if ok and selected_name:
            selected_node = next((node for node in available_nodes 
                                if node.name == selected_name), None)
            if selected_node:
                self.create_parent_child_relationship(selected_node)

    def create_parent_child_relationship(self, child_node):
        """Erstellt eine Eltern-Kind-Beziehung zu einem bestehenden Knoten"""
        try:
            # Partner finden (falls vorhanden)
            partner = self.find_partner()
            
            if partner:
                # Kind zur Partnerlinie hinzufügen
                if self.graph:
                    partnership_key = f"partnership_{self.name}_{partner.name}"
                    # Partnership-Knoten erstellen falls nicht vorhanden
                    if not self.graph.has_node(partnership_key):
                        self.graph.add_node(partnership_key, type="partnership")
                    
                    # Bestehende Verbindungen zum Kind entfernen (falls vorhanden)
                    edges_to_remove = []
                    for u, v in self.graph.edges():
                        if (u == child_node.name or v == child_node.name):
                            edges_to_remove.append((u, v))
                    
                    for u, v in edges_to_remove:
                        # Nur normale Verbindungen entfernen, nicht Partnerschaften
                        if self.graph.edges[u, v].get('type') != 'partner':
                            self.graph.remove_edge(u, v)
                    
                    # Neue Eltern-Kind-Verbindung erstellen
                    self.graph.add_edge(partnership_key, child_node.name, 
                                      type="parent-child", 
                                      color="#000000", 
                                      style="Durchgezogen")
                
                # Visuelle Verbindung erstellen/aktualisieren
                self.scene_ref.add_child_to_partnership(self, partner, child_node)
                
            else:
                # Kein Partner - direkte Eltern-Kind-Verbindung
                if self.graph:
                    # Bestehende normale Verbindungen entfernen
                    if self.graph.has_edge(self.name, child_node.name):
                        self.graph.remove_edge(self.name, child_node.name)
                    elif self.graph.has_edge(child_node.name, self.name):
                        self.graph.remove_edge(child_node.name, self.name)
                    
                    # Neue Eltern-Kind-Verbindung
                    self.graph.add_edge(self.name, child_node.name, 
                                      type="parent-child", 
                                      color="#000000", 
                                      style="Durchgezogen")
                
                # Bestehende visuelle Verbindung entfernen
                edges_to_remove = []
                for edge in list(self.edges):
                    if ((edge.source == self and edge.dest == child_node) or
                        (edge.source == child_node and edge.dest == self)):
                        edges_to_remove.append(edge)
                
                for edge in edges_to_remove:
                    edge.remove()
                
                # Neue Eltern-Kind-Kante erstellen
                parent_child_edge = EdgeItem(self, child_node, 
                                           QPen(Qt.black, 2, Qt.SolidLine))
                self.scene_ref.addItem(parent_child_edge)
            
            QMessageBox.information(None, tr("messages.success"), 
                                  tr("messages.child_added_successfully", 
                                     child=child_node.name, parent=self.name))
            
            # Undo-Funktionalität
            if hasattr(self.scene_ref, 'undo_stack'):
                self.scene_ref.undo_stack.append(
                    ("add_existing_as_child", self.name, child_node.name)
                )
                
        except Exception as e:
            QMessageBox.critical(None, tr("messages.error"), 
                               tr("messages.error_parent_child_relationship", error=str(e)))

    def convert_connection_to_parent_child(self, other_node):
        """Wandelt eine bestehende normale Verbindung in eine Eltern-Kind-Beziehung um"""
        if not self.scene_ref or not other_node:
            return False
            
        try:
            # Dialog zur Bestimmung wer Elternteil und wer Kind ist
            options = [
                tr("relationship_options.parent_of", parent=self.name, child=other_node.name),
                tr("relationship_options.parent_of", parent=other_node.name, child=self.name)
            ]
            
            choice, ok = QInputDialog.getItem(
                None,
                tr("dialogs.parent_child_relationship"),
                tr("dialogs.select_relationship_direction"),
                options,
                0,
                False
            )
            
            if ok:
                if choice == options[0]:
                    # self ist Elternteil, other_node ist Kind
                    return self.create_parent_child_relationship(other_node)
                else:
                    # other_node ist Elternteil, self ist Kind
                    return other_node.create_parent_child_relationship(self)
                    
            return False
        except Exception as e:
            print(f"Fehler beim Umwandeln zu Eltern-Kind-Beziehung: {e}")
            return False

    def add_child(self):
        """Korrigierte add_child Methode - verhindert Absturz wenn kein Partner vorhanden"""
        if not self.scene_ref:
            return
        
        dialog = PersonDialog(self.scene_ref)
        if dialog.exec_():
            name, birth, notes, photo, shape = dialog.get_data()
            pos = self.pos() + QPointF(self.size*2 + 20, self.size*2 + 20)
            child = NodeItem(name, birth, notes, photo, pos, self.graph, self.scene_ref, shape=shape, size=self.size)
            
            # Zuerst zur Szene hinzufügen
            self.scene_ref.addItem(child)
            
            # Partner finden (wenn vorhanden)
            partner = self.find_partner()
            
            if partner:
                # Kind zur Mitte der Partnerlinie verbinden
                if self.graph:
                    partnership_key = f"partnership_{self.name}_{partner.name}"
                    # Partnership-Knoten erstellen falls nicht vorhanden
                    if not self.graph.has_node(partnership_key):
                        self.graph.add_node(partnership_key, type="partnership")
                    self.graph.add_edge(partnership_key, name, type="parent-child", color="#000000", style="Durchgezogen")
                self.scene_ref.add_child_to_partnership(self, partner, child)
            else:
                # KORRIGIERT: Kein Partner - normale Verbindung, KEIN Absturz
                if self.graph:
                    self.graph.add_edge(self.name, name, type="parent-child", color="#000000", style="Durchgezogen")
                # Normale Edge erstellen statt partnership edge
                edge = EdgeItem(self, child, QPen(Qt.black, 2, Qt.SolidLine))
                self.scene_ref.addItem(edge)
            
            if hasattr(self.scene_ref, 'undo_stack'):
                self.scene_ref.undo_stack.append(("add_node", name, pos, birth, notes, photo, shape, self.size))


    def find_partner(self):
        """Korrigierte find_partner Methode - robustere Partner-Erkennung"""
        try:
            for edge in self.edges:
                # Sicherheitsprüfung für Edge-Existenz
                if not hasattr(edge, 'source') or not hasattr(edge, 'dest'):
                    continue
                    
                # Den anderen Knoten finden
                other_node = None
                if hasattr(edge, 'source') and hasattr(edge, 'dest'):
                    if edge.source == self:
                        other_node = edge.dest
                    elif edge.dest == self:
                        other_node = edge.source
                
                if other_node is None:
                    continue
                    
                # Prüfen ob es eine Partnerschaftsverbindung ist
                if isinstance(edge, PartnershipEdgeItem):
                    return other_node
                elif hasattr(edge, 'pen') and edge.pen.style() == Qt.DashLine and edge.pen.color() == QColor("#0000FF"):
                    return other_node
                    
            return None
        except Exception as e:
            print(f"Fehler in find_partner: {e}")
            return None

    def add_partner(self):
        if not self.scene_ref:
            return
        dialog = PersonDialog(self.scene_ref)
        if dialog.exec_():
            name, birth, notes, photo, shape = dialog.get_data()
            pos = self.pos() + QPointF(self.size*2 + 20, 0)
            partner = NodeItem(name, birth, notes, photo, pos, self.graph, self.scene_ref, shape=shape, size=self.size)
            self.scene_ref.addItem(partner)
            if self.graph:
                self.graph.add_edge(self.name, name, type="partner", color="#0000FF", style="dashed")
            
            # Spezielle Partnerschafts-Kante erstellen
            partnership_edge = PartnershipEdgeItem(self, partner)
            self.scene_ref.addItem(partnership_edge)
            
            if hasattr(self.scene_ref, 'undo_stack'):
                self.scene_ref.undo_stack.append(("add_node", name, pos, birth, notes, photo, shape, self.size))

    def edit_node(self):
        if not self.scene_ref:
            return
        dialog = PersonDialog(self.scene_ref, name=self.name, birth=self.birth, notes=self.notes, photo=self.photo, shape=self.shape)
        if dialog.exec_():
            old_name = self.name
            name, birth, notes, photo, shape = dialog.get_data()
            
            # Graph aktualisieren wenn Name geändert wurde
            if name != old_name and self.graph and old_name in self.graph.nodes:
                attrs = dict(self.graph.nodes[old_name])
                nx.relabel_nodes(self.graph, {old_name: name}, copy=False)
            
            self.name = name
            self.birth = birth
            self.notes = notes
            self.photo = photo
            self.shape = shape
            self.text.setPlainText(name)
            
            if self.graph and name in self.graph.nodes:
                self.graph.nodes[name].update({
                    "birth": birth,
                    "notes": notes,
                    "photo": photo,
                    "shape": shape,
                    "pos": [self.pos().x(), self.pos().y()],
                    "size": self.size
                })
            
            # Farbe ändern
            color = QColorDialog.getColor(self.color)
            if color.isValid():
                self.color = color
                self.graph.nodes[name]['color'] = color.name()
                print(f"NodeItem.edit_node: Name={name}, New Color={self.color.name()}")
            
            # Font ändern
            font, ok = QFontDialog.getFont(self.font)
            if ok:
                self.font = font
                self.text.setFont(font)
                if self.graph and name in self.graph.nodes:
                    self.graph.nodes[name].update({
                        'font_family': font.family(),
                        'font_size': font.pointSize(),
                        'font_weight': font.weight(),
                        'font_italic': font.italic()
                    })
                print(f"NodeItem.edit_node: Name={name}, Font={font.family()}, Size={font.pointSize()}, Weight={font.weight()}, Italic={font.italic()}")
            
            # Foto oder Farbe anwenden
            if photo:
                self.load_photo(photo)
            else:
                self.setBrush(QBrush(self.color))
                print(f"NodeItem.edit_node: Name={name}, No photo, applied Color={self.color.name()}")
            
            self.update_shape()

    def resize_node(self):
        old_size = self.size
        size, ok = QInputDialog.getInt(
            None, 
            tr("dialogs.resize_node"), 
            tr("dialogs.new_size"), 
            self.size, 20, 200
        )
        if ok:
            self.size = size
            if self.graph and self.name in self.graph.nodes:
                self.graph.nodes[self.name]['size'] = size
            self.update_shape()
            for edge in self.edges:
                edge.update_position()
            # Undo-Funktionalität hinzufügen
            if self.scene_ref and hasattr(self.scene_ref, 'undo_stack'):
                self.scene_ref.undo_stack.append(("resize_node", self.name, old_size, size))

    def delete_node(self):
        # Erst alle Kanten entfernen
        for edge in list(self.edges):
            edge.remove()
        
        # Dann aus Graph entfernen
        if self.graph and self.name in self.graph.nodes:
            self.graph.remove_node(self.name)
        
        # Schließlich aus Szene entfernen
        if self.scene():
            self.scene().removeItem(self)
        
        if self.scene_ref and hasattr(self.scene_ref, 'undo_stack'):
            self.scene_ref.undo_stack.append(("delete_node", self.name, self.pos(), self.birth, self.notes, self.photo, self.shape, self.size))

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionChange:
            for edge in self.edges:
                edge.update_position()
            if self.graph and self.name in self.graph.nodes:
                self.graph.nodes[self.name]['pos'] = [value.x(), value.y()]
        return super().itemChange(change, value)

class PartnershipEdgeItem(QGraphicsLineItem):
    """Spezielle Kante für Partnerschaften mit Mittelpunkt für Kinder"""
    def __init__(self, source: NodeItem, dest: NodeItem, pen=QPen(QColor("#0000FF"), 2, Qt.DashLine)):
        super().__init__()
        self.setFlag(self.ItemIsSelectable, True)
        self.source = source
        self.dest = dest
        self.pen = pen
        self.setPen(pen)
        self.source.edges.append(self)
        self.dest.edges.append(self)
        self.child_edges = []  # Kanten zu Kindern
        self.update_position()

    def get_midpoint(self):
        """Gibt den Mittelpunkt der Partnerlinie zurück"""
        src_pos = self.source.scenePos()
        dst_pos = self.dest.scenePos()
        return QPointF((src_pos.x() + dst_pos.x()) / 2, (src_pos.y() + dst_pos.y()) / 2)

    def update_position(self):
        src_pos = self.source.scenePos()
        dst_pos = self.dest.scenePos()
        self.setLine(src_pos.x(), src_pos.y(), dst_pos.x(), dst_pos.y())
        self.setZValue(-1)
        # Kind-Kanten aktualisieren
        for child_edge in self.child_edges:
            child_edge.update_position()
        self.update()

    def remove(self):
        # Alle Kind-Kanten entfernen
        for child_edge in list(self.child_edges):
            child_edge.remove()
        # Aus den Knotenlisten entfernen
        if self in self.source.edges:
            self.source.edges.remove(self)
        if self in self.dest.edges:
            self.dest.edges.remove(self)
        # Aus der Szene entfernen
        if self.scene():
            self.scene().removeItem(self)

    def setPen(self, pen):  # <- HIER HINZUFÜGEN
        """Korrigierte setPen Methode für EdgeItem"""
        super().setPen(pen)
        self.pen = pen

    def contextMenuEvent(self, event):
        """Erweiterte Kontextmenü-Methode mit Partnerschaftsoptionen"""
        menu = QMenu()
        add_child = menu.addAction(tr("context_menu.add_child"))
        convert_to_partnership = menu.addAction(tr("context_menu.convert_to_partnership"))
        convert_to_parent_child = menu.addAction(tr("context_menu.convert_to_parent_child"))
        change_color = menu.addAction(tr("context_menu.change_color"))
        change_style = menu.addAction(tr("context_menu.change_style"))
        delete = menu.addAction(tr("context_menu.delete"))
        
        action = menu.exec_(event.screenPos())
        
        if action == add_child:
            self.add_child()
        elif action == add_partner:
            self.add_partner()
        elif action == connect:
            if self.scene_ref:
                self.scene_ref.start_connection(self)
        elif action == convert_to_partnership:
            self.show_connection_conversion_dialog()
        elif action == convert_to_parent_child:
            self.convert_to_parent_child()
        elif action == change_color:
            self.change_color()
        elif action == change_style:
            self.change_line_style()
        elif action == delete:
            self.delete_partnership()

    def show_connection_conversion_dialog_enhanced(self):
        """Erweiterte Dialog-Optionen für Verbindungsumwandlung"""
        if not hasattr(self, 'scene_ref') or not self.scene_ref:
            return
            
        menu = QMenu()
        to_partnership = menu.addAction("Zu Partnerschaft umwandeln")
        to_parent_child = menu.addAction("Zu Eltern-Kind-Beziehung umwandeln")
        
        action = menu.exec_()
        
        if action == to_partnership:
            self.convert_to_partnership()
        elif action == to_parent_child:
            self.convert_to_parent_child()

    def convert_to_parent_child(self):
        """Wandelt eine normale Verbindung in eine Eltern-Kind-Beziehung um"""
        try:
            # Dialog zur Bestimmung der Richtung
            options = [
                tr("relationship_options.parent_of", parent=self.source.name, child=self.dest.name),
                tr("relationship_options.parent_of", parent=self.dest.name, child=self.source.name)
            ]
            
            choice, ok = QInputDialog.getItem(
                None,
                tr("dialogs.parent_child_relationship"),
                tr("dialogs.select_relationship_direction"),
                options,
                0,
                False
            )
            
            if ok:
                
                # Bestehende Verbindung entfernen
                if hasattr(self, 'graph') and self.graph:
                    if self.graph.has_edge(self.source.name, self.dest.name):
                        self.graph.remove_edge(self.source.name, self.dest.name)
                
                # Neue Eltern-Kind-Verbindung erstellen
                if choice == options[0]:
                    # source ist Elternteil
                    self.source.create_parent_child_relationship(self.dest)
                else:
                    # dest ist Elternteil
                    self.dest.create_parent_child_relationship(self.source)
                
                # Alte visuelle Verbindung entfernen
                self.remove()
                
                QMessageBox.information(
                    None, 
                    tr("messages.success"), 
                    tr("messages.connection_converted_successfully")
                )
                return True
        except Exception as e:
            QMessageBox.critical(
                None, 
                tr("messages.error"), 
                tr("messages.error_parent_child_relationship", error=str(e))
            )
            return False

    def show_connection_conversion_dialog(self):
        """Zeigt Dialog zur Auswahl einer Verbindung die zu Partnerschaft umgewandelt werden soll"""
        if not self.scene_ref:
            return
            
        # Alle normalen Verbindungen finden
        normal_connections = []
        for edge in self.edges:
            if isinstance(edge, EdgeItem):
                other_node = edge.dest if edge.source == self else edge.source
                if other_node and hasattr(other_node, 'name'):
                    normal_connections.append(other_node)
        
        if not normal_connections:
            QMessageBox.information(
                None, 
                tr("messages.info"), 
                tr("messages.no_connections_found")
            )
            return
        
        # Dialog zur Auswahl der zu konvertierenden Verbindung
        connection_names = [node.name for node in normal_connections]
        selected_name, ok = QInputDialog.getItem(
            None, 
            tr("dialogs.convert_connection"),
            tr("dialogs.select_connection_to_convert"),
            connection_names,
            0,
            False
        )
        
        if ok and selected_name:
            selected_node = next((node for node in normal_connections if node.name == selected_name), None)
            if selected_node:
                success = self.convert_connection_to_partnership(selected_node)
                if success:
                    QMessageBox.information(
                        None, 
                        tr("messages.success"), 
                        tr("messages.connection_to_partnership_success", name=selected_name)
                    )
                else:
                    QMessageBox.warning(
                        None, 
                        tr("messages.warning"), 
                        tr("messages.connection_conversion_failed")
                    )

    def convert_connection_to_partnership(self, other_node):
        """Wandelt eine bestehende normale Verbindung in eine Partnerschaft um"""
        if not self.scene_ref or not other_node:
            return False
            
        try:
            # Bestehende normale Kante finden und entfernen
            edge_to_remove = None
            for edge in list(self.edges):
                if isinstance(edge, EdgeItem):
                    if ((edge.source == self and edge.dest == other_node) or 
                        (edge.source == other_node and edge.dest == self)):
                        edge_to_remove = edge
                        break
            
            if edge_to_remove:
                # Graph-Kante entfernen
                if self.graph:
                    if self.graph.has_edge(self.name, other_node.name):
                        self.graph.remove_edge(self.name, other_node.name)
                    elif self.graph.has_edge(other_node.name, self.name):
                        self.graph.remove_edge(other_node.name, self.name)
                
                # Visuelle Kante entfernen
                edge_to_remove.remove()
                
                # Partnerschafts-Kante erstellen
                if self.graph:
                    self.graph.add_edge(self.name, other_node.name, type="partner", color="#0000FF", style="Gestrichelt")
                
                partnership_edge = PartnershipEdgeItem(self, other_node)
                self.scene_ref.addItem(partnership_edge)
                
                return True
            return False
        except Exception as e:
            print(f"Fehler beim Umwandeln zu Partnerschaft: {e}")
            return False

    def add_child_to_partnership(self, parent1: NodeItem, parent2: NodeItem, child: NodeItem):
        """Korrigierte Methode zum Hinzufügen eines Kindes zur Partnerlinie"""
        try:
            # Partnerschafts-Kante finden
            partnership_edge = None
            for edge in parent1.edges:
                if isinstance(edge, PartnershipEdgeItem):
                    if (edge.dest == parent2 or edge.source == parent2):
                        partnership_edge = edge
                        break
            
            if partnership_edge:
                # Kind-Kante zur Partnerschaft hinzufügen
                child_edge = ChildEdgeItem(partnership_edge, child)
                self.addItem(child_edge)
                partnership_edge.child_edges.append(child_edge)
            else:
                # FALLBACK: Wenn keine Partnerschafts-Kante gefunden wird
                print(f"Warnung: Keine Partnerschafts-Kante zwischen {parent1.name} und {parent2.name} gefunden")
                # Normale Kante zu einem der Eltern erstellen
                edge = EdgeItem(parent1, child, QPen(Qt.black, 2, Qt.SolidLine))
                self.addItem(edge)
        except Exception as e:
            print(f"Fehler in add_child_to_partnership: {e}")
            # FALLBACK: Normale Kante erstellen bei Fehler
            try:
                edge = EdgeItem(parent1, child, QPen(Qt.black, 2, Qt.SolidLine))
                self.addItem(edge)
            except Exception as fallback_error:
                print(f"Auch Fallback-Verbindung fehlgeschlagen: {fallback_error}")

    def change_color(self):
        """Farbe der Partnerlinie ändern"""
        color = QColorDialog.getColor(self.pen.color())
        if color.isValid():
            old_pen = self.pen
            self.pen = QPen(color, 2, self.pen.style())
            self.setPen(self.pen)

    def change_line_style(self):
        """Linienstil der Partnerlinie ändern"""
        dialog = LineStyleDialog()
        if dialog.exec_():
            style = dialog.get_style()
            old_pen = self.pen
            
            if style == "Durchgezogen":
                new_pen = QPen(self.pen.color(), 2, Qt.SolidLine)
            elif style == "Gestrichelt":
                new_pen = QPen(self.pen.color(), 2, Qt.DashLine)
            elif style == "Gepunktet":
                new_pen = QPen(self.pen.color(), 2, Qt.DotLine)
            elif style == "Strich-Punkt":
                new_pen = QPen(self.pen.color(), 2, Qt.DashDotLine)
            else:
                new_pen = QPen(self.pen.color(), 2, Qt.SolidLine)
            
            self.pen = new_pen
            self.setPen(new_pen)

    def delete_partnership(self):
        """Partnerschaft löschen"""
        self.remove()

class ChildEdgeItem(QGraphicsLineItem):
    """Spezielle Kante von Partnerlinie zu Kind"""
    def __init__(self, partnership: PartnershipEdgeItem, child: NodeItem):
        super().__init__()
        self.setFlag(self.ItemIsSelectable, True)
        self.partnership = partnership
        self.child = child
        self.pen = QPen(Qt.black, 2)
        self.setPen(QPen(QColor("black"), 2, Qt.SolidLine))
        self.child.edges.append(self)
        self.update_position()

    def setPen(self, pen):
        """Korrigierte setPen Methode für ChildEdgeItem"""
        super().setPen(pen)
        self.pen = pen  # <- DIESE ZEILE FEHLTE
        print(f"ChildEdgeItem.setPen: Child={self.child.name}, Style={pen.style()}, Color={pen.color().name()}")
        
    def update_position(self):
        midpoint = self.partnership.get_midpoint()
        child_pos = self.child.scenePos()
        self.setLine(midpoint.x(), midpoint.y(), child_pos.x(), child_pos.y())
        self.setZValue(-1)
        self.update()

    def remove(self):
        # Aus Kind-Kantenliste entfernen
        if self in self.child.edges:
            self.child.edges.remove(self)
        # Aus Partnership-Kantenliste entfernen
        if self in self.partnership.child_edges:
            self.partnership.child_edges.remove(self)
        # Aus der Szene entfernen
        if self.scene():
            self.scene().removeItem(self)

    def setPen(self, pen):  # <- HIER HINZUFÜGEN
        """Korrigierte setPen Methode für PartnershipEdgeItem"""  
        super().setPen(pen)
        self.pen = pen

    def contextMenuEvent(self, event):
        menu = QMenu()
        change_color = menu.addAction("Farbe ändern")
        change_style = menu.addAction("Linienstil ändern")
        delete = menu.addAction("Verbindung löschen")
        action = menu.exec_(event.screenPos())
        
        if action == change_color:
            color = QColorDialog.getColor(self.pen.color())
            if color.isValid():
                old_pen = self.pen
                self.pen = QPen(color, 2, self.pen.style())
                self.setPen(self.pen)
                
                # Graph aktualisieren
                scene_parent = self.get_scene_parent()
                if scene_parent and hasattr(scene_parent, 'graph'):
                    graph = scene_parent.graph
                    edge_key = f"partnership_{self.partnership.source.name}_{self.partnership.dest.name}"
                    if graph.has_edge(edge_key, self.child.name):
                        graph.edges[edge_key, self.child.name]['color'] = color.name()
                
                # Undo hinzufügen
                if self.scene() and hasattr(self.scene(), 'undo_stack'):
                    self.scene().undo_stack.append(("change_edge_color", f"partnership_{self.partnership.source.name}_{self.partnership.dest.name}", self.child.name, old_pen))
        
        elif action == change_style:
            self.change_line_style()
            
        elif action == delete:
            # Graph aktualisieren
            scene_parent = self.get_scene_parent()
            if scene_parent and hasattr(scene_parent, 'graph'):
                graph = scene_parent.graph
                edge_key = f"partnership_{self.partnership.source.name}_{self.partnership.dest.name}"
                if graph.has_edge(edge_key, self.child.name):
                    graph.remove_edge(edge_key, self.child.name)
            
            # Undo hinzufügen
            if self.scene() and hasattr(self.scene(), 'undo_stack'):
                self.scene().undo_stack.append(("delete_edge", f"partnership_{self.partnership.source.name}_{self.partnership.dest.name}", self.child.name, self.pen))
            
            self.remove()

    def get_scene_parent(self):
        """Hilfsmethode um scene parent zu finden"""
        scene_parent = None
        if self.scene() and hasattr(self.scene(), 'parent'):
            scene_parent = self.scene().parent
        elif self.child.scene_ref and hasattr(self.child.scene_ref, 'parent'):
            scene_parent = self.child.scene_ref.parent
        return scene_parent

    def change_line_style(self):
        """Dialog zum Ändern des Linienstils"""
        dialog = LineStyleDialog()
        if dialog.exec_():
            style = dialog.get_style()
            old_pen = self.pen
            
            # Neuen Pen mit gewähltem Stil erstellen
            if style == "Durchgezogen":
                new_pen = QPen(self.pen.color(), 2, Qt.SolidLine)
            elif style == "Gestrichelt":
                new_pen = QPen(self.pen.color(), 2, Qt.DashLine)
            elif style == "Gepunktet":
                new_pen = QPen(self.pen.color(), 2, Qt.DotLine)
            elif style == "Strich-Punkt":
                new_pen = QPen(self.pen.color(), 2, Qt.DashDotLine)
            else:
                new_pen = QPen(self.pen.color(), 2, Qt.SolidLine)
            
            self.pen = new_pen
            self.setPen(new_pen)
            
            # Graph aktualisieren
            scene_parent = self.get_scene_parent()
            if scene_parent and hasattr(scene_parent, 'graph'):
                graph = scene_parent.graph
                edge_key = f"partnership_{self.partnership.source.name}_{self.partnership.dest.name}"
                if graph.has_edge(edge_key, self.child.name):
                    graph.edges[edge_key, self.child.name]['style'] = style
            
            # Undo hinzufügen
            if self.scene() and hasattr(self.scene(), 'undo_stack'):
                self.scene().undo_stack.append(("change_edge_style", f"partnership_{self.partnership.source.name}_{self.partnership.dest.name}", self.child.name, old_pen))

    def setPen_corrected_for_ChildEdgeItem(self, pen):
        """Korrigierte setPen Methode für ChildEdgeItem"""
        super().setPen(pen)
        # KORRIGIERT: pen-Attribut auch intern speichern
        self.pen = pen
        print(f"ChildEdgeItem.setPen: Child={self.child.name}, Style={pen.style()}, Color={pen.color().name()}")

    # ZUSÄTZLICHE KORREKTUREN für EdgeItem Klasse:

    def setPen_corrected_for_EdgeItem(self, pen):
        """Korrigierte setPen Methode für EdgeItem"""
        super().setPen(pen)
        # KORRIGIERT: pen-Attribut auch intern speichern
        self.pen = pen

    def setPen_corrected_for_PartnershipEdgeItem(self, pen):
        """Korrigierte setPen Methode für PartnershipEdgeItem"""
        super().setPen(pen)
        # KORRIGIERT: pen-Attribut auch intern speichern
        self.pen = pen

class EdgeItem(QGraphicsLineItem):
    def __init__(self, source: NodeItem, dest: NodeItem, pen=QPen(Qt.black, 2)):
        super().__init__()
        self.setFlag(self.ItemIsSelectable, True)
        self.source = source
        self.dest = dest
        self.pen = pen
        self.setPen(pen)
        self.source.edges.append(self)
        self.dest.edges.append(self)
        self.update_position()

    def update_position(self):
        src_pos = self.source.scenePos()
        dst_pos = self.dest.scenePos()
        self.setLine(src_pos.x(), src_pos.y(), dst_pos.x(), dst_pos.y())
        self.setZValue(-1)
        self.update()

    def remove(self):
        # Aus den Knotenlisten entfernen
        if self in self.source.edges:
            self.source.edges.remove(self)
        if self in self.dest.edges:
            self.dest.edges.remove(self)
        
        # Aus der Szene entfernen
        if self.scene():
            self.scene().removeItem(self)

    def contextMenuEvent(self, event):
        menu = QMenu()
        change_color = menu.addAction(tr("context_menu.change_color"))
        change_style = menu.addAction(tr("context_menu.change_style"))
        delete = menu.addAction(tr("context_menu.delete_connection"))
        action = menu.exec_(event.screenPos())
        
        if action == change_color:
            color = QColorDialog.getColor(self.pen.color())
            if color.isValid():
                old_pen = self.pen
                self.pen = QPen(color, 2, self.pen.style())
                self.setPen(self.pen)
                
                # Graph aktualisieren
                scene_parent = self.get_scene_parent()
                if scene_parent and hasattr(scene_parent, 'graph'):
                    graph = scene_parent.graph
                    if graph.has_edge(self.source.name, self.dest.name):
                        graph.edges[self.source.name, self.dest.name]['color'] = color.name()
                
                # Undo hinzufügen
                if self.scene() and hasattr(self.scene(), 'undo_stack'):
                    self.scene().undo_stack.append(("change_edge_color", self.source.name, self.dest.name, old_pen))
        
        elif action == change_style:
            self.change_line_style()
            
        elif action == delete:
            # Graph aktualisieren
            scene_parent = self.get_scene_parent()
            if scene_parent and hasattr(scene_parent, 'graph'):
                graph = scene_parent.graph
                if graph.has_edge(self.source.name, self.dest.name):
                    graph.remove_edge(self.source.name, self.dest.name)
            
            # Undo hinzufügen
            if self.scene() and hasattr(self.scene(), 'undo_stack'):
                self.scene().undo_stack.append(("delete_edge", self.source.name, self.dest.name, self.pen))
            
            self.remove()

    def get_scene_parent(self):
        """Hilfsmethode um scene parent zu finden"""
        scene_parent = None
        if self.scene() and hasattr(self.scene(), 'parent'):
            scene_parent = self.scene().parent
        elif self.source.scene_ref and hasattr(self.source.scene_ref, 'parent'):
            scene_parent = self.source.scene_ref.parent
        return scene_parent

    def change_line_style(self):
        """Dialog zum Ändern des Linienstils"""
        dialog = LineStyleDialog()
        if dialog.exec_():
            style = dialog.get_style()
            old_pen = self.pen
            
            # Neuen Pen mit gewähltem Stil erstellen
            if style == "Durchgezogen":
                new_pen = QPen(self.pen.color(), 2, Qt.SolidLine)
            elif style == "Gestrichelt":
                new_pen = QPen(self.pen.color(), 2, Qt.DashLine)
            elif style == "Gepunktet":
                new_pen = QPen(self.pen.color(), 2, Qt.DotLine)
            elif style == "Strich-Punkt":
                new_pen = QPen(self.pen.color(), 2, Qt.DashDotLine)
            else:
                new_pen = QPen(self.pen.color(), 2, Qt.SolidLine)
            
            self.pen = new_pen
            self.setPen(new_pen)
            
            # Graph aktualisieren
            scene_parent = self.get_scene_parent()
            if scene_parent and hasattr(scene_parent, 'graph'):
                graph = scene_parent.graph
                if graph.has_edge(self.source.name, self.dest.name):
                    graph.edges[self.source.name, self.dest.name]['style'] = style
            
            # Undo hinzufügen
            if self.scene() and hasattr(self.scene(), 'undo_stack'):
                self.scene().undo_stack.append(("change_edge_style", self.source.name, self.dest.name, old_pen))

class LineStyleDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("dialogs.line_style"))
        layout = QVBoxLayout()
        
        self.style_combo = QComboBox()
        # Lokalisierte Linienstil-Namen
        styles = ["solid", "dashed", "dotted", "dash_dot"]
        for style_key in styles:
            self.style_combo.addItem(tr(f"line_styles.{style_key}"), style_key)
        
        self.style_combo.setCurrentIndex(0)  # Standard: Durchgezogen
        
        layout.addWidget(self.style_combo)
        
        self.ok_button = QPushButton(tr("dialogs.ok"))
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        
        self.setLayout(layout)

    def get_style(self):
        return self.style_combo.currentData()

class PersonDialog(QDialog):
    def __init__(self, scene, name="", birth="", notes="", photo=None, shape="rectangle"):
        super().__init__()
        self.setWindowTitle(tr("dialogs.person_data"))
        layout = QVBoxLayout()
        form = QFormLayout()
        
        self.name_edit = QLineEdit(name)
        self.birth_edit = QLineEdit(birth)
        self.notes_edit = QLineEdit(notes)
        self.photo_edit = QLineEdit(photo if photo else "")
        self.photo_button = QPushButton(tr("dialogs.select_photo"))
        self.photo_button.clicked.connect(self.select_photo)
        
        self.shape_combo = QComboBox()
        # Lokalisierte Shape-Namen
        shapes = ["rectangle", "ellipse", "triangle", "oval", "circle"]
        for shape_key in shapes:
            self.shape_combo.addItem(tr(f"shapes.{shape_key}"), shape_key)
        
        # Aktuellen Shape setzen
        for i in range(self.shape_combo.count()):
            if self.shape_combo.itemData(i) == shape:
                self.shape_combo.setCurrentIndex(i)
                break
        
        form.addRow(tr("dialogs.name"), self.name_edit)
        form.addRow(tr("dialogs.birth_date"), self.birth_edit)
        form.addRow(tr("dialogs.notes"), self.notes_edit)
        form.addRow(tr("dialogs.photo"), self.photo_edit)
        form.addRow(self.photo_button)
        form.addRow(tr("dialogs.shape"), self.shape_combo)
        
        layout.addLayout(form)
        
        self.ok_button = QPushButton(tr("dialogs.ok"))
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        
        self.setLayout(layout)

    def select_photo(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, 
            tr("dialogs.select_photo"), 
            filter=tr("file_filters.images")
        )
        if fname:
            self.photo_edit.setText(fname)

    def get_data(self):
        return (
            self.name_edit.text(),
            self.birth_edit.text(),
            self.notes_edit.text(),
            self.photo_edit.text() or None,
            self.shape_combo.currentData()  # Verwende Data statt Text für internationale Kompatibilität
        )

class TreeScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.parent = None  # wird später gesetzt
        self.pending_source = None
        self.undo_stack = []
        self.redo_stack = []

    def start_connection(self, node: NodeItem):
        self.pending_source = node

    def add_edge_visual(self, source: NodeItem, dest: NodeItem, pen=QPen(Qt.black, 2)):
        edge = EdgeItem(source, dest, pen)
        self.addItem(edge)
        if hasattr(self, 'undo_stack'):
            self.undo_stack.append(("add_edge", source.name, dest.name, pen))
            self.redo_stack.clear()

    def add_child_to_partnership(self, parent1: NodeItem, parent2: NodeItem, child: NodeItem):
        """Kind zur Partnerlinie hinzufügen"""
        # Partnerschafts-Kante finden
        partnership_edge = None
        for edge in parent1.edges:
            if isinstance(edge, PartnershipEdgeItem) and (edge.dest == parent2 or edge.source == parent2):
                partnership_edge = edge
                break
        
        if partnership_edge:
            # Kind-Kante zur Partnerschaft hinzufügen
            child_edge = ChildEdgeItem(partnership_edge, child)
            self.addItem(child_edge)
            partnership_edge.child_edges.append(child_edge)

    def mousePressEvent(self, event):
        """Korrigierte mousePressEvent Methode mit besserer Fehlerbehandlung"""
        try:
            item = self.itemAt(event.scenePos(), self.views()[0].transform())
            
            # Verbesserte Zielerkennung: Auch bei Text des NodeItem wird der NodeItem erkannt
            if isinstance(item, QGraphicsTextItem) and isinstance(item.parentItem(), NodeItem):
                item = item.parentItem()
            
            if isinstance(item, NodeItem) and self.pending_source:
                if item != self.pending_source:
                    # Sicherheitsprüfung vor Edge-Erstellung
                    if hasattr(self.pending_source, 'name') and hasattr(item, 'name'):
                        edge = EdgeItem(self.pending_source, item)
                        self.addItem(edge)
                        
                        if self.parent and hasattr(self.parent, 'graph'):
                            self.parent.graph.add_edge(
                                self.pending_source.name, 
                                item.name, 
                                type="custom", 
                                color="#000000",
                                style="Durchgezogen"
                            )
                        
                        if hasattr(self, 'undo_stack'):
                            self.undo_stack.append(("add_edge", self.pending_source.name, item.name, QPen(Qt.black, 2)))
                            self.redo_stack.clear()
                self.pending_source = None
            else:
                super().mousePressEvent(event)
        except Exception as e:
            print(f"Fehler in mousePressEvent: {e}")
            self.pending_source = None
            super().mousePressEvent(event)


class TreeEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang_manager = get_language_manager()
        self.setWindowTitle(tr("app_title"))
        self.graph = nx.DiGraph()
        self.scene = TreeScene()
        self.scene.parent = self
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setSceneRect(-1000, -1000, 2000, 2000)
        self.setCentralWidget(self.view)
        self.create_actions()
        self.resize(800, 600)

    def create_actions(self):
        menubar = self.menuBar()
        
        # Datei-Menü
        filem = menubar.addMenu(tr("menu.file"))
        load_act = QAction(tr("menu.load_json"), self, triggered=self.load_json)
        save_act = QAction(tr("menu.save_json"), self, triggered=self.save_json)
        export_png_act = QAction(tr("menu.export_png"), self, triggered=self.export_png)
        export_csv_act = QAction(tr("menu.export_csv"), self, triggered=self.export_csv)
        import_gedcom_act = QAction(tr("menu.import_gedcom"), self, triggered=self.import_gedcom)
        export_gedcom_act = QAction(tr("menu.export_gedcom"), self, triggered=self.export_gedcom)
        filem.addActions([load_act, save_act, export_png_act, export_csv_act, import_gedcom_act, export_gedcom_act])
        
        # Bearbeiten-Menü
        editm = menubar.addMenu(tr("menu.edit"))
        addn = QAction(tr("menu.add_node"), self, triggered=self.add_node)
        undo_act = QAction(tr("menu.undo"), self, triggered=self.undo)
        redo_act = QAction(tr("menu.redo"), self, triggered=self.redo)
        search_act = QAction(tr("menu.search_person"), self, triggered=self.search_person)
        editm.addActions([addn, undo_act, redo_act, search_act])
        
        # Sprache-Menü
        lang_menu = menubar.addMenu("Language / Sprache")
        for lang_code in self.lang_manager.get_available_languages():
            lang_name = "Deutsch" if lang_code == "de" else "English" if lang_code == "en" else lang_code
            lang_action = QAction(lang_name, self)
            lang_action.triggered.connect(lambda checked, code=lang_code: self.change_language(code))
            lang_menu.addAction(lang_action)

    def change_language(self, language_code: str):
        """Ändert die Sprache der Anwendung"""
        if self.lang_manager.set_language(language_code):
            # Menüs und UI-Elemente neu erstellen
            self.setWindowTitle(tr("app_title"))
            self.menuBar().clear()
            self.create_actions()
            
            # Nachricht über erfolgreiche Sprachänderung
            QMessageBox.information(
                self, 
                tr("messages.info"), 
                "Language changed successfully / Sprache erfolgreich geändert"
            )

    def add_node(self):
        dialog = PersonDialog(self.scene)
        if dialog.exec_():
            name, birth, notes, photo, shape = dialog.get_data()
            pos = QPointF(0, 0)
            node = NodeItem(name, birth, notes, photo, pos, self.graph, self.scene, shape=shape)
            self.scene.addItem(node)
            self.scene.undo_stack.append(("add_node", name, pos, birth, notes, photo, shape, DEFAULT_SIZE))
            self.scene.redo_stack.clear()

    def update_edge_style(self, edge, style):
        if isinstance(edge, ChildEdgeItem):
            pen = edge.pen()
            if style == "Gestrichelt":
                pen.setStyle(Qt.DashLine)
            elif style == "Gepunktet":
                pen.setStyle(Qt.DotLine)
            elif style == "Strich-Punkt":
                pen.setStyle(Qt.DashDotLine)
            else:
                pen.setStyle(Qt.SolidLine)
            edge.setPen(pen)
            partnership_key = f"partnership_{edge.partnership.source.name}_{edge.partnership.dest.name}"
            if self.graph.has_edge(partnership_key, edge.child.name):
                self.graph.edges[partnership_key, edge.child.name]['style'] = style
                print(f"TreeEditor.update_edge_style: Updated child edge {partnership_key} -> {edge.child.name}, Style={style}")
        elif isinstance(edge, EdgeItem):
            pen = edge.pen()
            if style == "Gestrichelt":
                pen.setStyle(Qt.DashLine)
            elif style == "Gepunktet":
                pen.setStyle(Qt.DotLine)
            elif style == "Strich-Punkt":
                pen.setStyle(Qt.DashDotLine)
            else:
                pen.setStyle(Qt.SolidLine)
            edge.setPen(pen)
            edge_key = (edge.source.name, edge.dest.name)
            if self.graph.has_edge(*edge_key):
                self.graph.edges[edge_key]['style'] = style
                print(f"TreeEditor.update_edge_style: Updated edge {edge_key}, Style={style}")
        elif isinstance(edge, PartnershipEdgeItem):
            pen = edge.pen()
            if style == "Gestrichelt":
                pen.setStyle(Qt.DashLine)
            elif style == "Gepunktet":
                pen.setStyle(Qt.DotLine)
            elif style == "Strich-Punkt":
                pen.setStyle(Qt.DashDotLine)
            else:
                pen.setStyle(Qt.SolidLine)
            edge.setPen(pen)
            edge_key = (edge.source.name, edge.dest.name)
            if self.graph.has_edge(*edge_key):
                self.graph.edges[edge_key]['style'] = style
                print(f"TreeEditor.update_edge_style: Updated partner edge {edge_key}, Style={style}")

    def save_json(self):
        """Korrigierte save_json Methode mit Lokalisierung"""
        fname, _ = QFileDialog.getSaveFileName(
            self, 
            tr("menu.save_json"), 
            filter=tr("file_filters.json")
        )
        if fname:
            try:
                # Positionen und Eigenschaften aller Knoten aktualisieren
                for item in self.scene.items():
                    if isinstance(item, NodeItem) and item.name in self.graph.nodes:
                        self.graph.nodes[item.name]['pos'] = [item.pos().x(), item.pos().y()]
                        self.graph.nodes[item.name]['color'] = item.color.name()
                        self.graph.nodes[item.name]['photo'] = item.photo
                        self.graph.nodes[item.name]['font_family'] = item.font.family()
                        self.graph.nodes[item.name]['font_size'] = item.font.pointSize()
                        self.graph.nodes[item.name]['font_weight'] = item.font.weight()
                        self.graph.nodes[item.name]['font_italic'] = item.font.italic()
                        self.graph.nodes[item.name]['shape'] = item.shape
                        self.graph.nodes[item.name]['size'] = item.size
                        print(f"TreeEditor.save_json: Saving node {item.name}, Color={item.color.name()}")
                
                # KORRIGIERT: Alle Kanten aus dem Graph entfernen und neu aufbauen
                # um sicherzustellen, dass die aktuellen visuellen Zustände gespeichert werden
                edges_to_remove = list(self.graph.edges(data=True))
                for u, v, data in edges_to_remove:
                    self.graph.remove_edge(u, v)
                
                # Kantenattribute aus visuellen Objekten neu aufbauen
                partnership_nodes_added = set()
                
                for item in self.scene.items():
                    if isinstance(item, PartnershipEdgeItem):
                        # Partnership-Kante speichern
                        edge_key = (item.source.name, item.dest.name)
                        style = self._get_style_name_from_pen(item.pen)
                        
                        self.graph.add_edge(
                            item.source.name,
                            item.dest.name,
                            type='partner',
                            color=item.pen.color().name(),
                            style=style
                        )
                        print(f"TreeEditor.save_json: Saving partner edge {edge_key}, Style={style}, Color={item.pen.color().name()}")
                        
                        # Partnership-Knoten für Kinder erstellen
                        partnership_key = f"partnership_{item.source.name}_{item.dest.name}"
                        if partnership_key not in partnership_nodes_added:
                            self.graph.add_node(partnership_key, type="partnership")
                            partnership_nodes_added.add(partnership_key)
                        
                        # Kind-Kanten von Partnerschaften speichern
                        for child_edge in item.child_edges:
                            child = child_edge.child
                            child_style = self._get_style_name_from_pen(child_edge.pen)
                            
                            self.graph.add_edge(
                                partnership_key, 
                                child.name, 
                                type="parent-child",
                                color=child_edge.pen.color().name(),
                                style=child_style
                            )
                            print(f"TreeEditor.save_json: Saving child edge {partnership_key} -> {child.name}, Style={child_style}, Color={child_edge.pen.color().name()}")
                    
                    elif isinstance(item, EdgeItem):
                        # Normale Kante speichern
                        edge_key = (item.source.name, item.dest.name)
                        style = self._get_style_name_from_pen(item.pen)
                        
                        self.graph.add_edge(
                            item.source.name,
                            item.dest.name,
                            type="custom",
                            color=item.pen.color().name(),
                            style=style
                        )
                        print(f"TreeEditor.save_json: Saving edge {edge_key}, Style={style}, Color={item.pen.color().name()}")
                        
                data = nx.node_link_data(self.graph)
                with open(fname, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                QMessageBox.information(
                    self, 
                    tr("messages.success"), 
                    tr("messages.saved_successfully")
                )
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    tr("messages.error"), 
                    tr("messages.error_saving", error=str(e))
                )


    def _get_style_name_from_pen(self, pen):
        """Hilfsmethode: Stil-Namen aus QPen ableiten"""
        if pen.style() == Qt.DashLine:
            return "Gestrichelt"
        elif pen.style() == Qt.DotLine:
            return "Gepunktet"
        elif pen.style() == Qt.DashDotLine:
            return "Strich-Punkt"
        else:
            return "Durchgezogen"

    def _get_pen_style_from_name(self, style_name):
        """Hilfsmethode: QPen-Stil aus Namen ableiten"""
        if style_name == "Gestrichelt":
            return Qt.DashLine
        elif style_name == "Gepunktet":
            return Qt.DotLine
        elif style_name == "Strich-Punkt":
            return Qt.DashDotLine
        else:
            return Qt.SolidLine


    def load_json(self):
        """Korrigierte load_json Methode mit Lokalisierung"""
        fname, _ = QFileDialog.getOpenFileName(
            self, 
            tr("menu.load_json"), 
            filter=tr("file_filters.json")
        )
        if fname:
            try:
                with open(fname, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                self.graph = nx.node_link_graph(data)
                self.scene.clear()
                
                # Knoten laden
                node_items = {}
                for n, attrs in self.graph.nodes(data=True):
                    if n.startswith("partnership_"):
                        continue
                    pos = QPointF(attrs.get('pos', [0, 0])[0], attrs.get('pos', [0, 0])[1])
                    color_name = attrs.get('color', '#ffffff')
                    node = NodeItem(
                        n, 
                        attrs.get('birth', ''), 
                        attrs.get('notes', ''), 
                        attrs.get('photo', None),
                        pos, 
                        self.graph, 
                        self.scene, 
                        shape=attrs.get('shape', 'rectangle'), 
                        size=attrs.get('size', DEFAULT_SIZE),
                        color=color_name,
                        font_family=attrs.get('font_family', 'Arial'),
                        font_size=attrs.get('font_size', 10),
                        font_weight=attrs.get('font_weight', QFont.Normal),
                        font_italic=attrs.get('font_italic', False)
                    )
                    print(f"TreeEditor.load_json: Loaded node {n}, Color={node.color.name()}")
                    
                    self.scene.addItem(node)
                    node_items[n] = node
                
                # KORRIGIERT: Kanten systematisch in der richtigen Reihenfolge laden
                partnership_edges = {}
                
                # 1. Zuerst alle Partnership-Kanten laden
                for u, v, attrs in self.graph.edges(data=True):
                    if attrs.get('type') == 'partner' and u in node_items and v in node_items:
                        src = node_items[u]
                        dest = node_items[v]
                        style_name = attrs.get('style', 'Gestrichelt')
                        pen_style = self._get_pen_style_from_name(style_name)
                        color = QColor(attrs.get('color', '#0000FF'))
                        pen = QPen(color, 2, pen_style)
                        
                        edge = PartnershipEdgeItem(src, dest, pen)
                        self.scene.addItem(edge)
                        partnership_edges[f"partnership_{u}_{v}"] = edge
                        print(f"TreeEditor.load_json: Loaded partner edge {u} -> {v}, Style={style_name}, Color={color.name()}")
                
                # 2. Dann normale Parent-Child-Kanten (nicht von Partnerschaften)
                for u, v, attrs in self.graph.edges(data=True):
                    if (attrs.get('type') == 'parent-child' and 
                        not u.startswith("partnership_") and 
                        u in node_items and v in node_items):
                        
                        src = node_items[u]
                        dest = node_items[v]
                        style_name = attrs.get('style', 'Durchgezogen')
                        pen_style = self._get_pen_style_from_name(style_name)
                        color = QColor(attrs.get('color', '#000000'))
                        pen = QPen(color, 2, pen_style)
                        
                        edge = EdgeItem(src, dest, pen)
                        self.scene.addItem(edge)
                        print(f"TreeEditor.load_json: Loaded parent-child edge {u} -> {v}, Style={style_name}, Color={color.name()}")
                
                # 3. Custom-Kanten laden
                for u, v, attrs in self.graph.edges(data=True):
                    if (attrs.get('type') == 'custom' and 
                        u in node_items and v in node_items):
                        
                        src = node_items[u]
                        dest = node_items[v]
                        style_name = attrs.get('style', 'Durchgezogen')
                        pen_style = self._get_pen_style_from_name(style_name)
                        color = QColor(attrs.get('color', '#000000'))
                        pen = QPen(color, 2, pen_style)
                        
                        edge = EdgeItem(src, dest, pen)
                        self.scene.addItem(edge)
                        print(f"TreeEditor.load_json: Loaded custom edge {u} -> {v}, Style={style_name}, Color={color.name()}")
                
                # 4. Zuletzt Kind-Kanten von Partnerschaften laden
                for u, v, attrs in self.graph.edges(data=True):
                    if (attrs.get('type') == 'parent-child' and 
                        u.startswith("partnership_") and 
                        v in node_items):
                        
                        partnership_key = u
                        child = node_items[v]
                        partnership_edge = partnership_edges.get(partnership_key)
                        
                        if partnership_edge:
                            style_name = attrs.get('style', 'Durchgezogen')
                            pen_style = self._get_pen_style_from_name(style_name)
                            color = QColor(attrs.get('color', '#000000'))
                            pen = QPen(color, 2, pen_style)
                            
                            child_edge = ChildEdgeItem(partnership_edge, child)
                            child_edge.setPen(pen)
                            self.scene.addItem(child_edge)
                            partnership_edge.child_edges.append(child_edge)
                            print(f"TreeEditor.load_json: Loaded child edge {partnership_key} -> {v}, Style={style_name}, Color={color.name()}")
                
                QMessageBox.information(
                    self, 
                    tr("messages.success"), 
                    tr("messages.loaded_successfully")
                )
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    tr("messages.error"), 
                    tr("messages.error_loading", error=str(e))
                )

    def export_png(self):
        try:
            rect = self.scene.itemsBoundingRect()
            if rect.isEmpty():
                QMessageBox.information(
                    self, 
                    tr("messages.info"), 
                    tr("messages.no_objects_to_export")
                )
                return
            
            img = QPixmap(int(rect.width()) + 20, int(rect.height()) + 20)
            img.fill(Qt.white)
            painter = QPainter(img)
            painter.setRenderHint(QPainter.Antialiasing)
            target_rect = QRectF(10, 10, rect.width(), rect.height())
            self.scene.render(painter, target_rect, rect)
            painter.end()
            
            fname, _ = QFileDialog.getSaveFileName(
                self, 
                tr("menu.export_png"), 
                filter=tr("file_filters.png")
            )
            if fname:
                if img.save(fname, "PNG"):
                    QMessageBox.information(
                        self, 
                        tr("messages.success"), 
                        tr("messages.exported_successfully")
                    )
                else:
                    QMessageBox.critical(
                        self, 
                        tr("messages.error"), 
                        tr("messages.error_png_export", error="Fehler beim PNG-Export")
                    )
        except Exception as e:
            QMessageBox.critical(
                self, 
                tr("messages.error"), 
                tr("messages.error_png_export", error=str(e))
            )

    def export_csv(self):
        fname, _ = QFileDialog.getSaveFileName(
            self, 
            tr("menu.export_csv"), 
            filter=tr("file_filters.excel")
        )
        if fname:
            try:
                nodes_data = []
                for n, d in self.graph.nodes(data=True):
                    nodes_data.append({
                        "Name": n, 
                        "Geburtsdatum": d.get("birth", ""), 
                        "Notizen": d.get("notes", ""), 
                        "Form": d.get("shape", "rectangle")
                    })
                
                edges_data = []
                for u, v, d in self.graph.edges(data=True):
                    edges_data.append({
                        "Quelle": u, 
                        "Ziel": v, 
                        "Typ": d.get("type", "custom"), 
                        "Farbe": d.get("color", "#000000"),
                        "Stil": d.get("style", "Durchgezogen")
                    })
                
                nodes_df = pd.DataFrame(nodes_data)
                edges_df = pd.DataFrame(edges_data)
                
                with pd.ExcelWriter(fname, engine='openpyxl') as writer:
                    nodes_df.to_excel(writer, sheet_name="Personen", index=False)
                    edges_df.to_excel(writer, sheet_name="Beziehungen", index=False)
                
                QMessageBox.information(
                    self, 
                    tr("messages.success"), 
                    tr("messages.excel_exported_successfully")
                )
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    tr("messages.error"), 
                    tr("messages.error_excel_export", error=str(e))
                )

    def import_gedcom(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, 
            tr("menu.import_gedcom"), 
            filter=tr("file_filters.gedcom")
        )
        if fname:
            try:
                parser = Parser()
                parser.parse_file(fname)
                self.graph.clear()
                self.scene.clear()
                
                individuals = parser.get_element_list()
                node_items = {}
                
                # Individuen hinzufügen
                for individual in individuals:
                    if hasattr(individual, 'get_name') and individual.get_name():
                        names = individual.get_name()
                        if len(names) >= 2:
                            name = names[0] + " " + names[1]
                        else:
                            name = names[0] if names else "Unbekannt"
                        
                        birth = ""
                        if hasattr(individual, 'get_birth_data') and individual.get_birth_data():
                            birth_data = individual.get_birth_data()
                            birth = birth_data[0] if birth_data else ""
                        
                        pos = QPointF(0, 0)
                        node = NodeItem(name, birth, "", None, pos, self.graph, self.scene)
                        self.scene.addItem(node)
                        node_items[individual] = node
                
                QMessageBox.information(
                    self, 
                    tr("messages.success"), 
                    tr("messages.gedcom_imported_successfully")
                )
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    tr("messages.error"), 
                    tr("messages.error_gedcom_import", error=str(e))
                )

    def export_gedcom(self):
        QMessageBox.information(
            self, 
            tr("messages.info"), 
            tr("messages.gedcom_export_unavailable")
        )

    def undo(self):
        if self.scene.undo_stack:
            try:
                action = self.scene.undo_stack.pop()
                self.scene.redo_stack.append(action)
                
                if action[0] == "add_node":
                    _, name, pos, birth, notes, photo, shape, size = action
                    # Node entfernen
                    for item in list(self.scene.items()):
                        if isinstance(item, NodeItem) and item.name == name:
                            item.delete_node()
                            break
                
                elif action[0] == "delete_node":
                    _, name, pos, birth, notes, photo, shape, size = action
                    # Node wieder hinzufügen
                    node = NodeItem(name, birth, notes, photo, pos, self.graph, self.scene, shape=shape, size=size)
                    self.scene.addItem(node)
                
                elif action[0] == "add_edge":
                    _, src_name, dst_name, pen = action
                    # Edge entfernen
                    src = None
                    dst = None
                    for item in self.scene.items():
                        if isinstance(item, NodeItem):
                            if item.name == src_name:
                                src = item
                            elif item.name == dst_name:
                                dst = item
                    
                    if src and dst:
                        for edge in list(src.edges):
                            if (edge.source == src and edge.dest == dst) or (edge.source == dst and edge.dest == src):
                                edge.remove()
                                if self.graph.has_edge(src_name, dst_name):
                                    self.graph.remove_edge(src_name, dst_name)
                                break
                
                elif action[0] == "delete_edge":
                    _, src_name, dst_name, pen = action
                    # Edge wieder hinzufügen
                    src = None
                    dst = None
                    for item in self.scene.items():
                        if isinstance(item, NodeItem):
                            if item.name == src_name:
                                src = item
                            elif item.name == dst_name:
                                dst = item
                    
                    if src and dst:
                        edge = EdgeItem(src, dst, pen)
                        self.scene.addItem(edge)
                        self.graph.add_edge(src_name, dst_name, type="custom", color=pen.color().name())
                
                elif action[0] == "change_edge_color":
                    _, src_name, dst_name, old_pen = action
                    # Edge-Farbe zurücksetzen
                    for item in self.scene.items():
                        if isinstance(item, EdgeItem) and item.source.name == src_name and item.dest.name == dst_name:
                            current_pen = item.pen
                            item.pen = old_pen
                            item.setPen(old_pen)
                            if self.graph.has_edge(src_name, dst_name):
                                self.graph.edges[(src_name, dst_name)]['color'] = old_pen.color().name()
                            # Redo-Stack aktualisieren
                            self.scene.redo_stack[-1] = ("change_edge_color", src_name, dst_name, current_pen)
                            break

                elif action[0] == "change_edge_style":
                    _, src_name, dst_name, old_pen = action
                    # Edge-Stil zurücksetzen
                    for item in self.scene.items():
                        if isinstance(item, EdgeItem) and item.source.name == src_name and item.dest.name == dst_name:
                            current_pen = item.pen
                            item.pen = old_pen
                            item.setPen(old_pen)
                            if self.graph.has_edge(src_name, dst_name):
                                # Stil-Namen aus Pen-Stil ableiten
                                if old_pen.style() == Qt.DashLine:
                                    style_name = "Gestrichelt"
                                elif old_pen.style() == Qt.DotLine:
                                    style_name = "Gepunktet"
                                elif old_pen.style() == Qt.DashDotLine:
                                    style_name = "Strich-Punkt"
                                else:
                                    style_name = "Durchgezogen"
                                self.graph.edges[(src_name, dst_name)]['style'] = style_name
                            # Redo-Stack aktualisieren
                            self.scene.redo_stack[-1] = ("change_edge_style", src_name, dst_name, current_pen)
                            break

                elif action[0] == "resize_node":
                    _, name, old_size, new_size = action
                    # Node-Größe zurücksetzen
                    for item in self.scene.items():
                        if isinstance(item, NodeItem) and item.name == name:
                            item.size = old_size
                            if item.graph and name in item.graph.nodes:
                                item.graph.nodes[name]['size'] = old_size
                            item.update_shape()
                            for edge in item.edges:
                                edge.update_position()
                            # Redo-Stack aktualisieren
                            self.scene.redo_stack[-1] = ("resize_node", name, new_size, old_size)
                            break
                            
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    tr("messages.error"), 
                    tr("messages.error_undo", error=str(e))
                )

    def redo(self):
        if self.scene.redo_stack:
            try:
                action = self.scene.redo_stack.pop()
                self.scene.undo_stack.append(action)
                
                if action[0] == "add_node":
                    _, name, pos, birth, notes, photo, shape, size = action
                    # Node wieder hinzufügen
                    node = NodeItem(name, birth, notes, photo, pos, self.graph, self.scene, shape=shape, size=size)
                    self.scene.addItem(node)
                
                elif action[0] == "delete_node":
                    _, name, pos, birth, notes, photo, shape, size = action
                    # Node entfernen
                    for item in list(self.scene.items()):
                        if isinstance(item, NodeItem) and item.name == name:
                            item.delete_node()
                            break
                
                elif action[0] == "add_edge":
                    _, src_name, dst_name, pen = action
                    # Edge wieder hinzufügen
                    src = None
                    dst = None
                    for item in self.scene.items():
                        if isinstance(item, NodeItem):
                            if item.name == src_name:
                                src = item
                            elif item.name == dst_name:
                                dst = item
                    
                    if src and dst:
                        edge = EdgeItem(src, dst, pen)
                        self.scene.addItem(edge)
                        self.graph.add_edge(src_name, dst_name, type="custom", color=pen.color().name())
                
                elif action[0] == "delete_edge":
                    _, src_name, dst_name, pen = action
                    # Edge entfernen
                    src = None
                    dst = None
                    for item in self.scene.items():
                        if isinstance(item, NodeItem):
                            if item.name == src_name:
                                src = item
                            elif item.name == dst_name:
                                dst = item
                    
                    if src and dst:
                        for edge in list(src.edges):
                            if (edge.source == src and edge.dest == dst) or (edge.source == dst and edge.dest == src):
                                edge.remove()
                                if self.graph.has_edge(src_name, dst_name):
                                    self.graph.remove_edge(src_name, dst_name)
                                break
                
                elif action[0] == "change_edge_color":
                    _, src_name, dst_name, pen = action
                    # Edge-Farbe ändern
                    for item in self.scene.items():
                        if isinstance(item, EdgeItem) and item.source.name == src_name and item.dest.name == dst_name:
                            item.pen = pen
                            item.setPen(pen)
                            if self.graph.has_edge(src_name, dst_name):
                                self.graph.edges[(src_name, dst_name)]['color'] = pen.color().name()
                            break

                elif action[0] == "change_edge_style":
                    _, src_name, dst_name, pen = action
                    # Edge-Stil ändern
                    for item in self.scene.items():
                        if isinstance(item, EdgeItem) and item.source.name == src_name and item.dest.name == dst_name:
                            item.pen = pen
                            item.setPen(pen)
                            if self.graph.has_edge(src_name, dst_name):
                                # Stil-Namen aus Pen-Stil ableiten
                                if pen.style() == Qt.DashLine:
                                    style_name = "Gestrichelt"
                                elif pen.style() == Qt.DotLine:
                                    style_name = "Gepunktet"
                                elif pen.style() == Qt.DashDotLine:
                                    style_name = "Strich-Punkt"
                                else:
                                    style_name = "Durchgezogen"
                                self.graph.edges[(src_name, dst_name)]['style'] = style_name
                            break

                elif action[0] == "resize_node":
                    _, name, old_size, new_size = action
                    # Node-Größe wiederherstellen
                    for item in self.scene.items():
                        if isinstance(item, NodeItem) and item.name == name:
                            item.size = new_size
                            if item.graph and name in item.graph.nodes:
                                item.graph.nodes[name]['size'] = new_size
                            item.update_shape()
                            for edge in item.edges:
                                edge.update_position()
                            break
                            
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    tr("messages.error"), 
                    tr("messages.error_redo", error=str(e))
                )

    def search_person(self):
        name, ok = QInputDialog.getText(
            self, 
            tr("dialogs.search"), 
            tr("dialogs.search_name")
        )
        if ok and name:
            found = False
            for item in self.scene.items():
                if isinstance(item, NodeItem) and name.lower() in item.name.lower():
                    self.scene.clearSelection()
                    item.setSelected(True)
                    self.view.centerOn(item)
                    found = True
                    break
            
            if not found:
                QMessageBox.information(
                    self, 
                    tr("messages.info"), 
                    tr("messages.person_not_found")
                )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = TreeEditor()
    editor.show()
    sys.exit(app.exec_())
