export interface BrewLog {
  id: string;
  date: string;
  bean: string;
  method: string;
  rating: number;
  taste: 'Balanced' | 'Sour' | 'Bitter' | 'Watery' | 'Astringent';
  dose: number;
  water: number;
  temp: number;
  time: string;
  grind: string;
  grinder: string;
  brewer?: string;
  yield?: number;
  flavorTags: string[];
  notes: string;
}

export let mockBrewLogs: BrewLog[] = [
  {
    id: '1',
    date: '2026-03-12',
    bean: 'Finca La Esperanza',
    method: 'V60',
    rating: 4,
    taste: 'Balanced',
    dose: 15,
    water: 250,
    temp: 96,
    time: '2:30',
    grind: '22 clicks',
    grinder: 'Comandante C40',
    brewer: 'Hario V60',
    flavorTags: ['Chocolate', 'Nutty', 'Caramel'],
    notes: 'Great cup! Sweet and balanced. Perfect extraction.'
  },
  {
    id: '2',
    date: '2026-03-11',
    bean: 'Yirgacheffe Konga',
    method: 'AeroPress',
    rating: 3,
    taste: 'Sour',
    dose: 14,
    water: 200,
    temp: 94,
    time: '2:00',
    grind: '20 clicks',
    grinder: 'Comandante C40',
    brewer: 'AeroPress',
    flavorTags: ['Lemon', 'Citrus'],
    notes: 'Too bright and sharp. Under-extracted — need to go finer next time.'
  },
  {
    id: '3',
    date: '2026-03-10',
    bean: 'Finca La Esperanza',
    method: 'V60',
    rating: 2,
    taste: 'Bitter',
    dose: 15,
    water: 250,
    temp: 98,
    time: '3:00',
    grind: '18 clicks',
    grinder: 'Comandante C40',
    brewer: 'Hario V60',
    flavorTags: ['Bitter', 'Astringent'],
    notes: 'Too bitter. Over-extracted. Grind coarser and lower temp.'
  },
  {
    id: '4',
    date: '2026-03-09',
    bean: 'El Paraiso Lychee',
    method: 'Chemex',
    rating: 5,
    taste: 'Balanced',
    dose: 30,
    water: 500,
    temp: 95,
    time: '4:00',
    grind: '24 clicks',
    grinder: 'Comandante C40',
    brewer: 'Chemex 6-cup',
    flavorTags: ['Floral', 'Stone fruit', 'Honey'],
    notes: 'Incredible! Complex, sweet, and floral. Perfect for this bean.'
  },
  {
    id: '5',
    date: '2026-03-08',
    bean: 'Yirgacheffe Konga',
    method: 'V60',
    rating: 3,
    taste: 'Watery',
    dose: 13,
    water: 220,
    temp: 93,
    time: '2:15',
    grind: '26 clicks',
    grinder: 'Comandante C40',
    brewer: 'Hario V60',
    flavorTags: ['Citrus', 'Clean'],
    notes: 'Weak and watery. Need to increase dose or grind finer.'
  },
  {
    id: '6',
    date: '2026-03-07',
    bean: 'Colombian Huila',
    method: 'French Press',
    rating: 4,
    taste: 'Balanced',
    dose: 30,
    water: 500,
    temp: 96,
    time: '4:00',
    grind: '28 clicks',
    grinder: 'Comandante C40',
    brewer: 'Bodum French Press',
    flavorTags: ['Chocolate', 'Nutty', 'Creamy'],
    notes: 'Rich and full-bodied. Great morning brew.'
  },
  {
    id: '7',
    date: '2026-03-06',
    bean: 'El Paraiso Lychee',
    method: 'AeroPress',
    rating: 4,
    taste: 'Balanced',
    dose: 16,
    water: 220,
    temp: 88,
    time: '1:30',
    grind: '16 clicks',
    grinder: 'Comandante C40',
    brewer: 'AeroPress',
    flavorTags: ['Floral', 'Berry', 'Honey'],
    notes: 'Sweet and clean. Lower temp really brings out the floral notes.'
  },
  {
    id: '8',
    date: '2026-03-05',
    bean: 'Colombian Huila',
    method: 'V60',
    rating: 3,
    taste: 'Bitter',
    dose: 15,
    water: 250,
    temp: 97,
    time: '2:45',
    grind: '20 clicks',
    grinder: 'Comandante C40',
    brewer: 'Hario V60',
    flavorTags: ['Chocolate', 'Earthy'],
    notes: 'Slightly over-extracted. Tone down the temperature.'
  }
];

export const beans = [
  'Finca La Esperanza',
  'Yirgacheffe Konga',
  'El Paraiso Lychee',
  'Colombian Huila',
  'Ethiopian Natural',
  'Kenya AA'
];

export const methods = [
  'V60',
  'AeroPress',
  'Chemex',
  'French Press',
  'Espresso',
  'Moka Pot'
];

export const grinders = [
  'Comandante C40',
  'Baratza Encore',
  'Timemore C2',
  '1Zpresso JX-Pro',
  'Fellow Ode'
];

export const brewers = [
  'Hario V60',
  'AeroPress',
  'Chemex 6-cup',
  'Bodum French Press',
  'Kalita Wave',
  'Fellow Stagg'
];

export const flavorOptions = [
  'Citrus', 'Berry', 'Chocolate', 'Nutty', 'Floral',
  'Honey', 'Caramel', 'Stone fruit', 'Spicy', 'Earthy',
  'Clean', 'Creamy', 'Lemon', 'Tart', 'Bitter', 'Astringent'
];

export const tasteOptions = [
  { value: 'Sour', label: 'Sour / acidic' },
  { value: 'Bitter', label: 'Bitter / harsh' },
  { value: 'Watery', label: 'Watery / thin' },
  { value: 'Astringent', label: 'Astringent / dry' },
  { value: 'Balanced', label: 'Balanced' }
] as const;
