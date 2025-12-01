// Type definitions for Vuetify 3.x
declare module 'vuetify/lib' {
  import { Component, ComponentPublicInstance } from 'vue';

  interface VuetifyOptions extends ComponentOptionsBase {
    vuetify?: any;
  }

  interface ComponentPublicInstanceWithMixins<
    Props,
    RawBindings,
    D,
    C,
    E,
    F,
    G,
    H,
    I,
    K,
    L,
    M,
    O,
    P,
    R,
    S,
    T,
    U
  > extends ComponentPublicInstance<Props> {
    $vuetify: any;
  }
}