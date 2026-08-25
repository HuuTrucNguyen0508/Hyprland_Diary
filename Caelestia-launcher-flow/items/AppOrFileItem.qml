import QtQuick
import Quickshell
import Caelestia.Config
import qs.components
import qs.modules.launcher.items

// ListView delegate that shows either an app or a file hit.
Item {
    id: root

    required property var modelData
    required property ScreenState screenState
    required property var list

    implicitHeight: Tokens.sizes.launcher.itemHeight

    anchors.left: parent?.left
    anchors.right: parent?.right

    Loader {
        id: loader

        anchors.fill: parent
        sourceComponent: root.modelData?.kind === "file" ? fileComp : appComp

        onLoaded: root.applyModel()
    }

    onModelDataChanged: root.applyModel()

    function applyModel(): void {
        if (!loader.item || !root.modelData)
            return;

        if (root.modelData.kind === "file") {
            loader.item.modelData = root.modelData;
            loader.item.list = root.list;
        } else {
            loader.item.modelData = root.modelData.entry ?? root.modelData;
            loader.item.screenState = root.screenState;
        }
    }

    Component {
        id: appComp

        AppItem {
            screenState: root.screenState
        }
    }

    Component {
        id: fileComp

        FileItem {
            list: root.list
        }
    }
}
