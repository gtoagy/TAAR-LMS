import type { Component } from 'vue'

export type SidebarLinkAction = 'commandPalette' | 'login' | 'logout'

export interface SidebarLink {
	label: string
	icon: string | Component
	to?: string
	action?: SidebarLinkAction
	shortcut?: string
	panel?: string
	count?: number
	onlyMobile?: boolean
	activeFor?: string[]
	condition?: () => boolean
	/** Orden en la barra inferior del móvil (1 a 4). Sin él, va a «Más». */
	pestana?: number
	/** La etiqueta que cabe debajo de un icono, si la de siempre no. */
	etiquetaCorta?: string
}
