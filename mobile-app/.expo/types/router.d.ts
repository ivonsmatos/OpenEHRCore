/* eslint-disable */
import * as Router from 'expo-router';

export * from 'expo-router';

declare module 'expo-router' {
  export namespace ExpoRouter {
    export interface __routes<T extends string = string> extends Record<string, unknown> {
      StaticRoutes: `/` | `/(auth)` | `/(auth)/login` | `/(tabs)` | `/(tabs)/` | `/(tabs)/appointments` | `/(tabs)/notifications` | `/(tabs)/profile` | `/(tabs)/records` | `/_sitemap` | `/appointments` | `/appointments/new` | `/login` | `/notifications` | `/profile` | `/records` | `/records/exams` | `/records/prescriptions`;
      DynamicRoutes: `/appointments/${Router.SingleRoutePart<T>}`;
      DynamicRouteTemplate: `/appointments/[id]`;
    }
  }
}
