import type { GameState, Message } from './types';

export const INITIAL_MESSAGES: Message[] = [
  { id: 1, sender: 'system', text: '系统已初始化。后室连接已建立。' },
  { id: 2, sender: 'dm', text: '你在一个潮湿的黄色房间里醒来。荧光灯的嗡嗡声震耳欲聋。你看到北边和东边有出口。' }
];

export const INITIAL_GAME_STATE: GameState = {
  level: "Level 1",
  attributes: {
    STR: 12,
    DEX: 14,
    CON: 13,
    INT: 16,
    WIS: 10,
    CHA: 8
  },
  vitals: {
    hp: 18,
    maxHp: 20,
    sanity: 85,
    maxSanity: 100
  },
  inventory: [
    { id: '1', name: '杏仁水', icon: '💧', quantity: 3, description: '一瓶散发着甜杏仁味的淡黄色液体。在这个地方，它是生命的源泉。', category: 'resource' },
    { id: '2', name: '手电筒', icon: '🔦', quantity: 1, description: '一个结实的手电筒，电池电量似乎还很足。能照亮前方未知的黑暗。', category: 'tool' },
    { id: '3', name: '大砍刀', icon: '🔪', quantity: 1, description: '一把生锈但依然锋利的大砍刀，是对付实体的好帮手。', category: 'weapon' },
    { id: '4', name: '急救包', icon: '❤️', quantity: 2, description: '包含绷带、消毒水和止痛药的标准急救包。', category: 'medical' },
    { id: '5', name: '压缩饼干', icon: '🍪', quantity: 5, description: '虽然口感像木屑，但能提供大量热量。', category: 'resource' },
    { id: '6', name: '撬棍', icon: '🔧', quantity: 1, description: '物理学圣剑，无论是开门还是敲人都在行。', category: 'tool' },
    { id: '7', name: '旧照片', icon: '📷', quantity: 1, description: '一张模糊的照片，依稀能分辨出一个微笑的人影，看着它让你感到莫名的悲伤。', category: 'document' },
    { id: '8', name: '生锈的钥匙', icon: '🗝️', quantity: 1, description: '不知道能打开哪扇门，但在后室里，钥匙总是有用的。', category: 'tool' },
    { id: '9', name: '无线电', icon: '📻', quantity: 1, description: '只能发出沙沙的白噪音，偶尔似乎能听到有人在低语。', category: 'tool' },
    { id: '10', name: '幸运硬币', icon: '🪙', quantity: 1, description: '一枚古老的金币，正面是笑脸，反面是哭脸。', category: 'special' },
    { id: '11', name: '皇家口粮', icon: '🥫', quantity: 1, description: '极其实验性的食物，据说味道好极了，但副作用未知。', category: 'resource' },
    { id: '12', name: '灭火器', icon: '🧯', quantity: 1, description: '沉重但可靠，可以用来扑灭火焰或作为钝器。', category: 'tool' },
    { id: '13', name: '录音带', icon: '📼', quantity: 1, description: '上面写着“不要听”，这让你更想找个播放器来听听。', category: 'document' },
    { id: '14', name: '损坏的指南针', icon: '🧭', quantity: 1, description: '指针疯狂地旋转，在这里方向是没有意义的。', category: 'special' },
    { id: '15', name: '瓶装闪电', icon: '⚡', quantity: 1, description: '玻璃瓶里跳动着蓝色的电弧，投掷出去可能造成巨大伤害。', category: 'weapon' },
    { id: '16', name: '液体痛苦', icon: '☠️', quantity: 1, description: '深红色的粘稠液体，以此物命名是有原因的。千万别喝。', category: 'special' },
    { id: '17', name: '摄像机', icon: '📹', quantity: 1, description: '电池还能撑一会，也许能记录下什么重要的东西。', category: 'tool' },
    { id: '18', name: '圣水', icon: '🏺', quantity: 1, description: '也许对某些邪恶实体有效？或者只是一瓶普通的自来水。', category: 'special' },
    { id: '19', name: '神秘纸条', icon: '📄', quantity: 1, description: '上面潦草地写着：“它就在你后面。”', category: 'document' },
    { id: '20', name: '瑞士军刀', icon: '⚔️', quantity: 1, description: '多功能工具，虽然每一项功能都不算顶尖，但胜在全面。', category: 'tool' },
    { id: '21', name: '电池', icon: '🔋', quantity: 4, description: '通用的AA电池，在这个没有充电插座的地方是硬通货。', category: 'resource' },
    null, null, null, null, null, null, null, null, null, null, null, null, null, null, null
  ]
};
