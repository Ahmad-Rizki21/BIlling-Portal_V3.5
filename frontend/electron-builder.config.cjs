module.exports = {
  appId: 'com.artacom.billing',
  productName: 'Artacom Billing System',
  copyright: 'Copyright © 2024 Artacom',
  directories: {
    output: 'release',
    buildResources: 'build'
  },
  files: [
    'dist/**/*',
    'electron/**/*',
    'package.json'
  ],
  win: {
    target: [
      {
        target: 'nsis',
        arch: ['x64']
      },
      {
        target: 'portable',
        arch: ['x64']
      }
    ],
    icon: 'public/icon_darkmode.ico',
    artifactName: '${productName}-${version}-${os}-${arch}.${ext}',
    signAndEditExecutable: false
  },
  nsis: {
    oneClick: false,
    allowToChangeInstallationDirectory: true,
    allowElevation: true,
    runAfterFinish: true,
    createDesktopShortcut: true,
    createStartMenuShortcut: true,
    shortcutName: 'Artacom Billing System',
    installerIcon: 'public/icon_darkmode.ico',
    uninstallerIcon: 'public/icon_darkmode.ico',
    perMachine: false,
    deleteAppDataOnUninstall: false
  },
  portable: {
    artifactName: '${productName}-${version}-portable.${ext}'
  }
};
