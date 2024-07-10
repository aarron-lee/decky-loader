import {
  DialogBody,
  DialogButton,
  DialogControlsSection,
  GamepadEvent,
  Menu,
  MenuItem,
  ReorderableEntry,
  ReorderableList,
  showContextMenu,
} from 'decky-frontend-lib';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaDownload, FaEllipsisH, FaRecycle } from 'react-icons/fa';

import { InstallType } from '../../../../plugin';
import {
  StorePluginVersion,
  getPluginList,
  requestMultiplePluginInstalls,
  requestPluginInstall,
} from '../../../../store';
import { useSetting } from '../../../../utils/hooks/useSetting';
import { useDeckyState } from '../../../DeckyState';

function labelToName(pluginLabel: string, pluginVersion?: string): string {
  return pluginVersion ? pluginLabel.substring(0, pluginLabel.indexOf(` - ${pluginVersion}`)) : pluginLabel;
}

async function reinstallPlugin(pluginName: string, currentVersion?: string) {
  const serverData = await getPluginList();
  const remotePlugin = serverData?.find((x) => x.name == pluginName);
  if (remotePlugin && remotePlugin.versions?.length > 0) {
    const currentVersionData = remotePlugin.versions.find((version) => version.name == currentVersion);
    if (currentVersionData) requestPluginInstall(pluginName, currentVersionData, InstallType.REINSTALL);
  }
}

function PluginInteractables(props: { entry: ReorderableEntry<PluginData> }) {
  const data = props.entry.data;
  const { t } = useTranslation();
  let pluginName = labelToName(props.entry.label, data?.version);

  const showCtxMenu = (e: MouseEvent | GamepadEvent) => {
    showContextMenu(
      <Menu label={t('PluginListIndex.plugin_actions')}>
        <MenuItem onSelected={() => window.DeckyPluginLoader.importPlugin(pluginName, data?.version)}>
          {t('PluginListIndex.reload')}
        </MenuItem>
        <MenuItem
          onSelected={() =>
            window.DeckyPluginLoader.uninstallPlugin(
              pluginName,
              t('UnofficialPluginLoader.plugin_uninstall.title', { name: pluginName }),
              t('UnofficialPluginLoader.plugin_uninstall.button'),
              t('UnofficialPluginLoader.plugin_uninstall.desc', { name: pluginName }),
            )
          }
        >
          {t('PluginListIndex.uninstall')}
        </MenuItem>
      </Menu>,
      e.currentTarget ?? window,
    );
  };

  return (
    <>
      {data?.update ? (
        <DialogButton
          style={{ height: '40px', minWidth: '60px', marginRight: '10px' }}
          onClick={() => requestPluginInstall(pluginName, data?.update as StorePluginVersion, InstallType.UPDATE)}
          onOKButton={() => requestPluginInstall(pluginName, data?.update as StorePluginVersion, InstallType.UPDATE)}
        >
          <div style={{ display: 'flex', minWidth: '180px', justifyContent: 'space-between', alignItems: 'center' }}>
            {t('PluginListIndex.update_to', { name: data?.update?.name })}
            <FaDownload style={{ paddingLeft: '1rem' }} />
          </div>
        </DialogButton>
      ) : (
        <DialogButton
          style={{ height: '40px', minWidth: '60px', marginRight: '10px' }}
          onClick={() => reinstallPlugin(pluginName, data?.version)}
          onOKButton={() => reinstallPlugin(pluginName, data?.version)}
        >
          <div style={{ display: 'flex', minWidth: '180px', justifyContent: 'space-between', alignItems: 'center' }}>
            {t('PluginListIndex.reinstall')}
            <FaRecycle style={{ paddingLeft: '1rem' }} />
          </div>
        </DialogButton>
      )}
      <DialogButton
        style={{
          height: '40px',
          width: '40px',
          padding: '10px 12px',
          minWidth: '40px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        }}
        onClick={showCtxMenu}
        onOKButton={showCtxMenu}
      >
        <FaEllipsisH />
      </DialogButton>
    </>
  );
}

type PluginData = {
  update?: StorePluginVersion;
  version?: string;
};

export default function PluginList() {
  const { plugins, updates, pluginOrder, setPluginOrder } = useDeckyState();
  const [_, setPluginOrderSetting] = useSetting<string[]>(
    'pluginOrder',
    plugins.map((plugin) => plugin.name),
  );
  const { t } = useTranslation();

  useEffect(() => {
    window.DeckyPluginLoader.checkPluginUpdates();
  }, []);

  const [pluginEntries, setPluginEntries] = useState<ReorderableEntry<PluginData>[]>([]);

  useEffect(() => {
    setPluginEntries(
      plugins.map((plugin) => {
        return {
          label: plugin.version ? `${plugin.name} - ${plugin.version}` : plugin.name,
          data: {
            update: updates?.get(plugin.name),
            version: plugin.version,
          },
          position: pluginOrder.indexOf(plugin.name),
        };
      }),
    );
  }, [plugins, updates]);

  if (plugins.length === 0) {
    return (
      <div>
        <p>{t('PluginListIndex.no_plugin')}</p>
      </div>
    );
  }

  function onSave(entries: ReorderableEntry<PluginData>[]) {
    const newOrder = entries.map((entry) => labelToName(entry.label, entry?.data?.version));
    console.log(newOrder);
    setPluginOrder(newOrder);
    setPluginOrderSetting(newOrder);
  }

  return (
    <DialogBody>
      {updates && updates.size > 0 && (
        <DialogButton
          onClick={() =>
            requestMultiplePluginInstalls(
              [...updates.entries()].map(([plugin, selectedVer]) => ({
                installType: InstallType.UPDATE,
                plugin,
                selectedVer,
              })),
            )
          }
          style={{
            position: 'absolute',
            top: '57px',
            right: '2.8vw',
            width: 'auto',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          {t('PluginListIndex.update_all', { count: updates.size })}
          <FaDownload style={{ paddingLeft: '1rem' }} />
        </DialogButton>
      )}
      <DialogControlsSection style={{ marginTop: 0 }}>
        <ReorderableList<PluginData> entries={pluginEntries} onSave={onSave} interactables={PluginInteractables} />
      </DialogControlsSection>
    </DialogBody>
  );
}
