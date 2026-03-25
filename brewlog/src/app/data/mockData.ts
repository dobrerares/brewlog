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
    date: '2026-03-19',
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
    notes: 'Great cup! Sweet and balanced.'
  },
  {
    id: '2',
    date: '2026-03-18',
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
    notes: 'Too bright. Under-extracted.'
  },
  {
    id: '3',
    date: '2026-03-17',
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
    notes: 'Incredible! Complex and sweet.'
  }
];

export const beans = [
  'Finca La Esperanza',
  'Yirgacheffe Konga',
  'El Paraiso Lychee',
  'Colombian Huila',
  'Ethiopian Natural'
];

export const methods = [
  'V60',
  'AeroPress',
  'Chemex',
  'French Press',
  'Espresso'
];

export const grinders = [
  'Comandante C40',
  'Baratza Encore',
  'Timemore C2',
  '1Zpresso JX-Pro'
];

export const brewers = [
  'Hario V60',
  'AeroPress',
  'Chemex 6-cup',
  'Bodum French Press'
];

export const flavorOptions = [
  'Citrus', 'Berry', 'Chocolate', 'Nutty', 'Floral',
  'Honey', 'Caramel', 'Stone fruit', 'Spicy', 'Earthy',
  'Clean', 'Creamy', 'Lemon', 'Tart', 'Bitter'
];

export const tasteOptions = [
  { value: 'Sour', label: 'Sour / acidic' },
  { value: 'Bitter', label: 'Bitter / harsh' },
  { value: 'Watery', label: 'Watery / thin' },
  { value: 'Astringent', label: 'Astringent / dry' },
  { value: 'Balanced', label: 'Balanced' }
] as const;
