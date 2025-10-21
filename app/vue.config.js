const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  pluginOptions: {
    electronBuilder: {
      builderOptions: {
        appId: "com.artacom.billingftth",
        productName: "Artacom FTTH Billing",
        copyright: "Copyright © 2024 Artacom",
        win: {
          target: "nsis", // Membuat installer .exe
          icon: "src/assets/icon.ico" // Pastikan Anda punya file icon.ico di sini
        },
        nsis: {
          oneClick: false, // Izinkan user memilih direktori instalasi
          allowToChangeInstallationDirectory: true
        }
      }
    }
  }
})