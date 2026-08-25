import QtQuick
import Quickshell
import Caelestia.Config
import qs.components
import qs.services
import qs.modules.launcher.services
import qs.modules.launcher.items

// ListView delegate for app / file / calc / web / url rows.
Item {
    id: root

    required property var modelData
    required property ScreenState screenState
    required property var list

    implicitHeight: Tokens.sizes.launcher.itemHeight

    anchors.left: parent?.left
    anchors.right: parent?.right

    readonly property bool isApp: !modelData?.kind || modelData.kind === "app"
    readonly property string extraKind: modelData?.kind ?? ""

    Loader {
        id: loader

        anchors.fill: parent
        sourceComponent: root.isApp ? appComp : extraComp

        onLoaded: root.applyModel()
    }

    onModelDataChanged: {
        // Reload component when switching between app and extra kinds.
        loader.sourceComponent = root.isApp ? appComp : extraComp;
        root.applyModel();
    }

    function applyModel(): void {
        if (!loader.item || !root.modelData)
            return;

        if (root.isApp) {
            loader.item.modelData = root.modelData.entry ?? root.modelData;
            loader.item.screenState = root.screenState;
        } else {
            loader.item.modelData = root.modelData;
            loader.item.list = root.list;
        }
    }

    function activate(): void {
        const data = root.modelData;
        if (!data)
            return;

        if (root.isApp) {
            Apps.launch(data.entry ?? data);
        } else if (data.kind === "file" && data.path) {
            Quickshell.execDetached(["xdg-open", data.path]);
        } else if (data.kind === "runner") {
            Runner.activate(data);
        } else if (data.kind === "window") {
            Windows.activate(data);
        } else {
            Extras.activate(data);
        }
        root.screenState.launcher = false;
    }

    Component {
        id: appComp

        AppItem {
            screenState: root.screenState
        }
    }

    Component {
        id: extraComp

        ExtraItem {
            list: root.list
            onActivated: root.activate()
        }
    }
}
