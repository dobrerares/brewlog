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

export const mockBrewLogs: BrewLog[] = [
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
  },
  {
    id: '9',
    date: '2026-03-04',
    bean: 'Kenya AA',
    method: 'V60',
    rating: 5,
    taste: 'Balanced',
    dose: 16,
    water: 260,
    temp: 94,
    time: '2:40',
    grind: '21 clicks',
    grinder: '1Zpresso JX-Pro',
    brewer: 'Hario V60',
    flavorTags: ['Berry', 'Citrus', 'Honey'],
    notes: 'Juicy acidity with clean sweetness. Best cup from this lot so far.'
  },
  {
    id: '10',
    date: '2026-03-03',
    bean: 'Ethiopian Natural',
    method: 'AeroPress',
    rating: 4,
    taste: 'Balanced',
    dose: 17,
    water: 230,
    temp: 90,
    time: '1:50',
    grind: '17 clicks',
    grinder: 'Timemore C2',
    brewer: 'AeroPress',
    flavorTags: ['Berry', 'Floral', 'Stone fruit'],
    notes: 'Round and fruit-forward. Short steep improved clarity.'
  },
  {
    id: '11',
    date: '2026-03-02',
    bean: 'Colombian Huila',
    method: 'Espresso',
    rating: 3,
    taste: 'Astringent',
    dose: 18,
    water: 36,
    temp: 93,
    time: '0:30',
    grind: '8 clicks',
    grinder: 'Baratza Encore',
    brewer: 'Fellow Stagg',
    flavorTags: ['Chocolate', 'Bitter'],
    notes: 'Slight channeling and dry finish. Needs distribution work.'
  },
  {
    id: '12',
    date: '2026-03-01',
    bean: 'Yirgacheffe Konga',
    method: 'Chemex',
    rating: 4,
    taste: 'Balanced',
    dose: 32,
    water: 520,
    temp: 95,
    time: '4:20',
    grind: '25 clicks',
    grinder: 'Comandante C40',
    brewer: 'Chemex 6-cup',
    flavorTags: ['Lemon', 'Floral', 'Clean'],
    notes: 'Bright but controlled. Paper rinse made a noticeable difference.'
  },
  {
    id: '13',
    date: '2026-02-28',
    bean: 'Ethiopian Natural',
    method: 'French Press',
    rating: 3,
    taste: 'Watery',
    dose: 28,
    water: 520,
    temp: 94,
    time: '4:30',
    grind: '30 clicks',
    grinder: 'Timemore C2',
    brewer: 'Bodum French Press',
    flavorTags: ['Berry', 'Tart'],
    notes: 'Pleasant fruit but thin body. Increase dose next run.'
  },
  {
    id: '14',
    date: '2026-02-27',
    bean: 'Kenya AA',
    method: 'Moka Pot',
    rating: 4,
    taste: 'Balanced',
    dose: 18,
    water: 180,
    temp: 96,
    time: '3:30',
    grind: '14 clicks',
    grinder: '1Zpresso JX-Pro',
    brewer: 'Fellow Stagg',
    flavorTags: ['Chocolate', 'Caramel', 'Spicy'],
    notes: 'Dense and sweet with low bitterness. Good milk drink base.'
  },
  {
    id: '15',
    date: '2026-02-26',
    bean: 'Finca La Esperanza',
    method: 'V60',
    rating: 5,
    taste: 'Balanced',
    dose: 15,
    water: 255,
    temp: 95,
    time: '2:35',
    grind: '23 clicks',
    grinder: 'Comandante C40',
    brewer: 'Hario V60',
    flavorTags: ['Caramel', 'Chocolate', 'Honey'],
    notes: 'Sweet and layered with a long clean finish. Repeat recipe.'
  },
  {
    id: '16',
    date: '2026-02-25',
    bean: 'Kenya AA',
    method: 'AeroPress',
    rating: 2,
    taste: 'Sour',
    dose: 15,
    water: 220,
    temp: 85,
    time: '1:20',
    grind: '19 clicks',
    grinder: 'Baratza Encore',
    brewer: 'AeroPress',
    flavorTags: ['Citrus', 'Tart'],
    notes: 'Sharp and underdeveloped. Raise temperature and steep longer.'
  },
  {
    id: '17',
    date: '2026-02-24',
    bean: 'El Paraiso Lychee',
    method: 'V60',
    rating: 5,
    taste: 'Balanced',
    dose: 15,
    water: 250,
    temp: 92,
    time: '2:25',
    grind: '21 clicks',
    grinder: 'Comandante C40',
    brewer: 'Hario V60',
    flavorTags: ['Floral', 'Honey', 'Stone fruit'],
    notes: 'Elegant cup with bright florals and long sweetness.'
  },
  {
    id: '18',
    date: '2026-02-23',
    bean: 'Colombian Huila',
    method: 'Chemex',
    rating: 3,
    taste: 'Bitter',
    dose: 30,
    water: 500,
    temp: 97,
    time: '4:10',
    grind: '23 clicks',
    grinder: 'Fellow Ode',
    brewer: 'Chemex 6-cup',
    flavorTags: ['Chocolate', 'Earthy'],
    notes: 'A touch dry and bitter at the finish. Lower temp next brew.'
  },
  {
    id: '19',
    date: '2026-02-22',
    bean: 'Ethiopian Natural',
    method: 'V60',
    rating: 4,
    taste: 'Balanced',
    dose: 16,
    water: 260,
    temp: 94,
    time: '2:45',
    grind: '22 clicks',
    grinder: 'Timemore C2',
    brewer: 'Kalita Wave',
    flavorTags: ['Berry', 'Floral', 'Clean'],
    notes: 'Sweet berry notes with crisp acidity and clean finish.'
  },
  {
    id: '20',
    date: '2026-02-21',
    bean: 'Kenya AA',
    method: 'French Press',
    rating: 4,
    taste: 'Balanced',
    dose: 32,
    water: 520,
    temp: 95,
    time: '4:00',
    grind: '29 clicks',
    grinder: 'Baratza Encore',
    brewer: 'Bodum French Press',
    flavorTags: ['Berry', 'Chocolate', 'Creamy'],
    notes: 'Full body with dark fruit and cacao sweetness.'
  },
  {
    id: '21',
    date: '2026-02-20',
    bean: 'Finca La Esperanza',
    method: 'AeroPress',
    rating: 3,
    taste: 'Watery',
    dose: 14,
    water: 240,
    temp: 91,
    time: '1:40',
    grind: '20 clicks',
    grinder: '1Zpresso JX-Pro',
    brewer: 'AeroPress',
    flavorTags: ['Caramel', 'Clean'],
    notes: 'Pleasant but thin. Increase dose and reduce bypass water.'
  },
  {
    id: '22',
    date: '2026-02-19',
    bean: 'Yirgacheffe Konga',
    method: 'Moka Pot',
    rating: 4,
    taste: 'Balanced',
    dose: 17,
    water: 170,
    temp: 95,
    time: '3:20',
    grind: '13 clicks',
    grinder: 'Comandante C40',
    brewer: 'Fellow Stagg',
    flavorTags: ['Lemon', 'Honey', 'Spicy'],
    notes: 'Concentrated and lively; excellent as a short cup.'
  },
  {
    id: '23',
    date: '2026-02-18',
    bean: 'El Paraiso Lychee',
    method: 'Espresso',
    rating: 2,
    taste: 'Astringent',
    dose: 18,
    water: 34,
    temp: 94,
    time: '0:27',
    grind: '7 clicks',
    grinder: 'Fellow Ode',
    brewer: 'Fellow Stagg',
    flavorTags: ['Floral', 'Bitter', 'Astringent'],
    notes: 'Harsh finish and uneven extraction. Needs coarser grind and better prep.'
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
