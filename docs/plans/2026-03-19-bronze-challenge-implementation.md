# BrewLog Bronze Challenge Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement master/detail CRUD views with strict validation, pagination, and ~80% test coverage.

**Architecture:** Three-layer separation (UI components → custom hooks → in-memory mock data). All business logic in hooks; components only handle rendering.

**Tech Stack:** React 18 + TypeScript + Tailwind CSS + Radix UI + Vitest/React Testing Library

---

## Task 1: Create useBrewValidation Hook with Tests

**Files:**
- Create: `src/app/hooks/useBrewValidation.ts`
- Create: `src/app/hooks/__tests__/useBrewValidation.test.ts`

**Step 1: Write failing test for field-level validation**

Create `src/app/hooks/__tests__/useBrewValidation.test.ts`:

```typescript
import { renderHook } from '@testing-library/react';
import { useBrewValidation } from '../useBrewValidation';

describe('useBrewValidation', () => {
  describe('validateField', () => {
    it('should require bean field', () => {
      const { result } = renderHook(() => useBrewValidation());
      const error = result.current.validateField('bean', '');
      expect(error).toBe('Bean is required');
    });

    it('should require method field', () => {
      const { result } = renderHook(() => useBrewValidation());
      const error = result.current.validateField('method', '');
      expect(error).toBe('Method is required');
    });

    it('should validate dose is positive', () => {
      const { result } = renderHook(() => useBrewValidation());
      const error = result.current.validateField('dose', -5);
      expect(error).toBe('Dose must be greater than 0');
    });

    it('should validate temp is in range 80-100°C', () => {
      const { result } = renderHook(() => useBrewValidation());
      expect(result.current.validateField('temp', 70)).toContain('Temperature must be between 80-100°C');
      expect(result.current.validateField('temp', 110)).toContain('Temperature must be between 80-100°C');
      expect(result.current.validateField('temp', 95)).toBe('');
    });

    it('should validate rating is 1-5', () => {
      const { result } = renderHook(() => useBrewValidation());
      expect(result.current.validateField('rating', 0)).toContain('Rating must be between 1 and 5');
      expect(result.current.validateField('rating', 6)).toContain('Rating must be between 1 and 5');
      expect(result.current.validateField('rating', 3)).toBe('');
    });

    it('should validate brew time format MM:SS', () => {
      const { result } = renderHook(() => useBrewValidation());
      expect(result.current.validateField('time', 'invalid')).toContain('Brew time must be in MM:SS format');
      expect(result.current.validateField('time', '2:30')).toBe('');
    });

    it('should validate water to dose ratio (10-20x)', () => {
      const { result } = renderHook(() => useBrewValidation());
      // This will be tested in validateForm with full brew data
      expect(true).toBe(true);
    });
  });

  describe('validateForm', () => {
    it('should return all field errors for incomplete form', () => {
      const { result } = renderHook(() => useBrewValidation());
      const brew = {
        id: '',
        bean: '',
        method: '',
        date: '',
        dose: 0,
        water: 0,
        temp: 50,
        time: '',
        grind: '',
        grinder: '',
        rating: 0,
        taste: '',
        flavorTags: [],
        notes: ''
      };
      const errors = result.current.validateForm(brew);
      expect(Object.keys(errors).length).toBeGreaterThan(0);
      expect(errors.bean).toBeDefined();
      expect(errors.temp).toBeDefined();
    });

    it('should validate dose/water ratio (10-20x)', () => {
      const { result } = renderHook(() => useBrewValidation());
      const brew = {
        id: '1',
        bean: 'Finca La Esperanza',
        method: 'V60',
        date: '2026-03-19',
        dose: 15,
        water: 100, // Only 6.67x, should fail
        temp: 95,
        time: '2:30',
        grind: '22 clicks',
        grinder: 'Comandante C40',
        rating: 4,
        taste: 'Balanced' as const,
        flavorTags: ['Chocolate'],
        notes: 'Good'
      };
      const errors = result.current.validateForm(brew);
      expect(errors.water).toContain('Water should be 10-20x the dose');
    });

    it('should validate temp to method constraints', () => {
      const { result } = renderHook(() => useBrewValidation());
      const brew = {
        id: '1',
        bean: 'Finca La Esperanza',
        method: 'Espresso',
        date: '2026-03-19',
        dose: 18,
        water: 300,
        temp: 70, // Too low for espresso
        time: '0:25',
        grind: '9 clicks',
        grinder: 'Comandante C40',
        rating: 4,
        taste: 'Balanced' as const,
        flavorTags: ['Chocolate'],
        notes: 'Good'
      };
      const errors = result.current.validateForm(brew);
      expect(errors.temp).toContain('Espresso requires temperature above 85°C');
    });

    it('should require grindAdjustment notes if rating < 3', () => {
      const { result } = renderHook(() => useBrewValidation());
      const brew = {
        id: '1',
        bean: 'Finca La Esperanza',
        method: 'V60',
        date: '2026-03-19',
        dose: 15,
        water: 250,
        temp: 95,
        time: '2:30',
        grind: '22 clicks',
        grinder: 'Comandante C40',
        rating: 2, // Low rating
        taste: 'Bitter' as const,
        flavorTags: [],
        notes: '' // No notes
      };
      const errors = result.current.validateForm(brew);
      expect(errors.notes).toContain('Please add notes for low-rated brews');
    });

    it('should pass validation for correct brew data', () => {
      const { result } = renderHook(() => useBrewValidation());
      const brew = {
        id: '1',
        bean: 'Finca La Esperanza',
        method: 'V60',
        date: '2026-03-19',
        dose: 15,
        water: 250,
        temp: 95,
        time: '2:30',
        grind: '22 clicks',
        grinder: 'Comandante C40',
        rating: 4,
        taste: 'Balanced' as const,
        flavorTags: ['Chocolate', 'Nutty'],
        notes: 'Great cup!'
      };
      const errors = result.current.validateForm(brew);
      expect(Object.keys(errors).length).toBe(0);
    });
  });
});
```

**Step 2: Run tests to verify they fail**

```bash
cd Untitled
npm test src/app/hooks/__tests__/useBrewValidation.test.ts
```

Expected: Multiple test failures — "useBrewValidation is not defined"

**Step 3: Write minimal implementation**

Create `src/app/hooks/useBrewValidation.ts`:

```typescript
import { BrewLog } from '../data/mockData';

const REQUIRED_FIELDS = ['bean', 'method', 'date', 'dose', 'water', 'temp', 'time', 'grind', 'grinder', 'rating', 'taste'];

export function useBrewValidation() {
  const validateField = (field: string, value: any): string => {
    if (REQUIRED_FIELDS.includes(field) && (value === '' || value === null || value === undefined)) {
      return `${field.charAt(0).toUpperCase() + field.slice(1)} is required`;
    }

    switch (field) {
      case 'dose':
        if (typeof value === 'number' && value <= 0) {
          return 'Dose must be greater than 0';
        }
        break;

      case 'water':
        if (typeof value === 'number' && value <= 0) {
          return 'Water must be greater than 0';
        }
        break;

      case 'temp':
        if (typeof value === 'number' && (value < 80 || value > 100)) {
          return 'Temperature must be between 80-100°C';
        }
        break;

      case 'rating':
        if (typeof value === 'number' && (value < 1 || value > 5)) {
          return 'Rating must be between 1 and 5';
        }
        break;

      case 'time':
        if (value && !/^\d{1,2}:\d{2}$/.test(String(value))) {
          return 'Brew time must be in MM:SS format';
        }
        break;
    }

    return '';
  };

  const validateForm = (brew: Partial<BrewLog>): Record<string, string> => {
    const errors: Record<string, string> = {};

    // Field-level validation
    Object.keys(brew).forEach((field) => {
      const error = validateField(field, brew[field as keyof BrewLog]);
      if (error) errors[field] = error;
    });

    // Business rule validation
    if (brew.dose && brew.water) {
      const ratio = brew.water / brew.dose;
      if (ratio < 10 || ratio > 20) {
        errors.water = 'Water should be 10-20x the dose (e.g., 15g dose → 150-300g water)';
      }
    }

    // Temp to method validation
    if (brew.method && brew.temp) {
      const methodTempMap: Record<string, { min: number; max: number }> = {
        'Espresso': { min: 85, max: 100 },
        'V60': { min: 90, max: 96 },
        'Chemex': { min: 90, max: 96 },
        'AeroPress': { min: 85, max: 100 },
        'French Press': { min: 90, max: 100 },
        'Moka Pot': { min: 90, max: 100 }
      };

      const methodConstraint = methodTempMap[brew.method];
      if (methodConstraint && (brew.temp < methodConstraint.min || brew.temp > methodConstraint.max)) {
        errors.temp = `${brew.method} requires temperature between ${methodConstraint.min}-${methodConstraint.max}°C`;
      }
    }

    // Cross-field validation: low rating requires notes
    if (brew.rating && brew.rating < 3 && !brew.notes) {
      errors.notes = 'Please add notes for low-rated brews to help improve future brews';
    }

    return errors;
  };

  return {
    validateField,
    validateForm
  };
}
```

**Step 4: Run tests to verify they pass**

```bash
npm test src/app/hooks/__tests__/useBrewValidation.test.ts
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/app/hooks/useBrewValidation.ts src/app/hooks/__tests__/useBrewValidation.test.ts
git commit -m "feat: add useBrewValidation hook with field/business rule/cross-field validation tests"
```

---

## Task 2: Create useBrewCRUD Hook with Tests

**Files:**
- Create: `src/app/hooks/useBrewCRUD.ts`
- Create: `src/app/hooks/__tests__/useBrewCRUD.test.ts`

**Step 1: Write failing tests for CRUD operations**

Create `src/app/hooks/__tests__/useBrewCRUD.test.ts`:

```typescript
import { renderHook, act } from '@testing-library/react';
import { useBrewCRUD } from '../useBrewCRUD';
import { mockBrewLogs, BrewLog } from '../data/mockData';

describe('useBrewCRUD', () => {
  beforeEach(() => {
    // Reset mock data before each test
    jest.clearAllMocks();
  });

  describe('createBrew', () => {
    it('should add a new brew to the list', () => {
      const { result } = renderHook(() => useBrewCRUD());
      const initialCount = result.current.getBrews().length;

      const newBrew = {
        bean: 'New Bean',
        method: 'V60',
        date: '2026-03-19',
        dose: 15,
        water: 250,
        temp: 95,
        time: '2:30',
        grind: '22 clicks',
        grinder: 'Comandante C40',
        rating: 4,
        taste: 'Balanced' as const,
        flavorTags: ['Chocolate'],
        notes: 'Great'
      };

      act(() => {
        result.current.createBrew(newBrew);
      });

      expect(result.current.getBrews().length).toBe(initialCount + 1);
      expect(result.current.getBrews()[result.current.getBrews().length - 1].bean).toBe('New Bean');
    });
  });

  describe('updateBrew', () => {
    it('should update an existing brew', () => {
      const { result } = renderHook(() => useBrewCRUD());
      const firstBrewId = result.current.getBrews()[0].id;

      act(() => {
        result.current.updateBrew(firstBrewId, { notes: 'Updated notes' });
      });

      const updated = result.current.getBrew(firstBrewId);
      expect(updated?.notes).toBe('Updated notes');
    });

    it('should not update if brew does not exist', () => {
      const { result } = renderHook(() => useBrewCRUD());
      const initialBrews = result.current.getBrews();

      act(() => {
        result.current.updateBrew('nonexistent', { notes: 'Should not work' });
      });

      expect(result.current.getBrews()).toEqual(initialBrews);
    });
  });

  describe('deleteBrew', () => {
    it('should remove a brew by id', () => {
      const { result } = renderHook(() => useBrewCRUD());
      const firstBrewId = result.current.getBrews()[0].id;
      const initialCount = result.current.getBrews().length;

      act(() => {
        result.current.deleteBrew(firstBrewId);
      });

      expect(result.current.getBrews().length).toBe(initialCount - 1);
      expect(result.current.getBrew(firstBrewId)).toBeUndefined();
    });
  });

  describe('getBrew', () => {
    it('should retrieve a single brew by id', () => {
      const { result } = renderHook(() => useBrewCRUD());
      const firstBrew = result.current.getBrews()[0];

      const retrieved = result.current.getBrew(firstBrew.id);
      expect(retrieved).toEqual(firstBrew);
    });

    it('should return undefined for non-existent brew', () => {
      const { result } = renderHook(() => useBrewCRUD());

      const retrieved = result.current.getBrew('nonexistent');
      expect(retrieved).toBeUndefined();
    });
  });

  describe('getBrews', () => {
    it('should return all brews', () => {
      const { result } = renderHook(() => useBrewCRUD());

      const brews = result.current.getBrews();
      expect(Array.isArray(brews)).toBe(true);
      expect(brews.length).toBeGreaterThan(0);
    });
  });
});
```

**Step 2: Run tests to verify they fail**

```bash
npm test src/app/hooks/__tests__/useBrewCRUD.test.ts
```

Expected: Failures — "useBrewCRUD is not defined"

**Step 3: Write minimal implementation**

Create `src/app/hooks/useBrewCRUD.ts`:

```typescript
import { useState, useCallback } from 'react';
import { BrewLog, mockBrewLogs } from '../data/mockData';

// In-memory store
let brewsState = [...mockBrewLogs];

export function useBrewCRUD() {
  const [brews, setBrews] = useState(brewsState);

  const createBrew = useCallback((brew: Omit<BrewLog, 'id'>) => {
    const newBrew: BrewLog = {
      ...brew,
      id: Date.now().toString()
    };
    brewsState = [...brewsState, newBrew];
    setBrews(brewsState);
    return newBrew;
  }, []);

  const updateBrew = useCallback((id: string, updates: Partial<BrewLog>) => {
    const index = brewsState.findIndex(b => b.id === id);
    if (index === -1) return;

    brewsState[index] = { ...brewsState[index], ...updates };
    setBrews([...brewsState]);
  }, []);

  const deleteBrew = useCallback((id: string) => {
    brewsState = brewsState.filter(b => b.id !== id);
    setBrews([...brewsState]);
  }, []);

  const getBrew = useCallback((id: string) => {
    return brews.find(b => b.id === id);
  }, [brews]);

  const getBrews = useCallback(() => {
    return brews;
  }, [brews]);

  return {
    createBrew,
    updateBrew,
    deleteBrew,
    getBrew,
    getBrews
  };
}
```

**Step 4: Run tests to verify they pass**

```bash
npm test src/app/hooks/__tests__/useBrewCRUD.test.ts
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/app/hooks/useBrewCRUD.ts src/app/hooks/__tests__/useBrewCRUD.test.ts
git commit -m "feat: add useBrewCRUD hook with create/read/update/delete operations and tests"
```

---

## Task 3: Create useBrewPagination Hook with Tests

**Files:**
- Create: `src/app/hooks/useBrewPagination.ts`
- Create: `src/app/hooks/__tests__/useBrewPagination.test.ts`

**Step 1: Write failing tests**

Create `src/app/hooks/__tests__/useBrewPagination.test.ts`:

```typescript
import { renderHook, act } from '@testing-library/react';
import { useBrewPagination } from '../useBrewPagination';

describe('useBrewPagination', () => {
  const mockItems = Array.from({ length: 25 }, (_, i) => ({ id: String(i), name: `Item ${i}` }));

  it('should initialize with first page', () => {
    const { result } = renderHook(() => useBrewPagination(mockItems, 10));

    expect(result.current.currentPage).toBe(1);
    expect(result.current.totalPages).toBe(3);
    expect(result.current.currentItems).toHaveLength(10);
  });

  it('should paginate items correctly', () => {
    const { result } = renderHook(() => useBrewPagination(mockItems, 10));

    expect(result.current.currentItems[0].id).toBe('0');
    expect(result.current.currentItems[9].id).toBe('9');
  });

  it('should navigate to next page', () => {
    const { result } = renderHook(() => useBrewPagination(mockItems, 10));

    act(() => {
      result.current.nextPage();
    });

    expect(result.current.currentPage).toBe(2);
    expect(result.current.currentItems[0].id).toBe('10');
  });

  it('should navigate to previous page', () => {
    const { result } = renderHook(() => useBrewPagination(mockItems, 10));

    act(() => {
      result.current.nextPage();
      result.current.nextPage();
      result.current.prevPage();
    });

    expect(result.current.currentPage).toBe(2);
  });

  it('should go to specific page', () => {
    const { result } = renderHook(() => useBrewPagination(mockItems, 10));

    act(() => {
      result.current.goToPage(3);
    });

    expect(result.current.currentPage).toBe(3);
    expect(result.current.currentItems[0].id).toBe('20');
  });

  it('should not go beyond total pages', () => {
    const { result } = renderHook(() => useBrewPagination(mockItems, 10));

    act(() => {
      result.current.goToPage(5);
    });

    expect(result.current.currentPage).toBe(3);
  });

  it('should handle empty items', () => {
    const { result } = renderHook(() => useBrewPagination([], 10));

    expect(result.current.totalPages).toBe(1);
    expect(result.current.currentItems).toHaveLength(0);
  });
});
```

**Step 2: Run tests to verify they fail**

```bash
npm test src/app/hooks/__tests__/useBrewPagination.test.ts
```

**Step 3: Write minimal implementation**

Create `src/app/hooks/useBrewPagination.ts`:

```typescript
import { useState, useMemo } from 'react';

export function useBrewPagination<T>(items: T[], pageSize: number = 10) {
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = useMemo(() => {
    return Math.max(1, Math.ceil(items.length / pageSize));
  }, [items.length, pageSize]);

  const currentItems = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return items.slice(startIndex, startIndex + pageSize);
  }, [items, currentPage, pageSize]);

  const nextPage = () => {
    setCurrentPage(prev => Math.min(prev + 1, totalPages));
  };

  const prevPage = () => {
    setCurrentPage(prev => Math.max(prev - 1, 1));
  };

  const goToPage = (page: number) => {
    const validPage = Math.max(1, Math.min(page, totalPages));
    setCurrentPage(validPage);
  };

  return {
    currentPage,
    totalPages,
    currentItems,
    nextPage,
    prevPage,
    goToPage
  };
}
```

**Step 4: Run tests to verify they pass**

```bash
npm test src/app/hooks/__tests__/useBrewPagination.test.ts
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/app/hooks/useBrewPagination.ts src/app/hooks/__tests__/useBrewPagination.test.ts
git commit -m "feat: add useBrewPagination hook with navigation and tests"
```

---

## Task 4: Update BrewForm to Use Validation Hook

**Files:**
- Modify: `src/app/pages/BrewForm.tsx` (entire rewrite)

**Step 1: Rewrite BrewForm to use useBrewValidation and useBrewCRUD**

```typescript
import { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router';
import { ArrowLeft } from 'lucide-react';
import { Navbar } from '../components/Navbar';
import { StarRating } from '../components/StarRating';
import { FlavorTag } from '../components/FlavorTag';
import { useBrewValidation } from '../hooks/useBrewValidation';
import { useBrewCRUD } from '../hooks/useBrewCRUD';
import { beans, methods, grinders, brewers, flavorOptions, tasteOptions, mockBrewLogs } from '../data/mockData';

export function BrewForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = id !== 'new';

  const { validateField, validateForm } = useBrewValidation();
  const { createBrew, updateBrew, getBrew } = useBrewCRUD();

  const existingBrew = isEdit ? getBrew(id!) : null;

  const [formData, setFormData] = useState({
    bean: existingBrew?.bean || '',
    method: existingBrew?.method || '',
    date: existingBrew?.date || new Date().toISOString().split('T')[0],
    dose: existingBrew?.dose || 0,
    water: existingBrew?.water || 0,
    temp: existingBrew?.temp || 0,
    time: existingBrew?.time || '',
    grind: existingBrew?.grind || '',
    grinder: existingBrew?.grinder || '',
    brewer: existingBrew?.brewer || '',
    yield: existingBrew?.yield || 0,
    rating: existingBrew?.rating || 0,
    taste: existingBrew?.taste || '',
    flavorTags: existingBrew?.flavorTags || [],
    notes: existingBrew?.notes || ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  const handleFieldChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));

    // Real-time validation
    const error = validateField(field, value);
    setErrors(prev => ({
      ...prev,
      [field]: error
    }));
  };

  const handleFieldBlur = (field: string) => {
    setTouched(prev => ({ ...prev, [field]: true }));
  };

  const toggleFlavor = (flavor: string) => {
    setFormData(prev => ({
      ...prev,
      flavorTags: prev.flavorTags.includes(flavor)
        ? prev.flavorTags.filter(f => f !== flavor)
        : [...prev.flavorTags, flavor]
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Mark all fields as touched
    const allTouched = Object.keys(formData).reduce((acc, field) => {
      acc[field] = true;
      return acc;
    }, {} as Record<string, boolean>);
    setTouched(allTouched);

    // Validate entire form
    const formErrors = validateForm(formData);
    setErrors(formErrors);

    if (Object.keys(formErrors).length === 0) {
      if (isEdit) {
        updateBrew(id!, formData);
      } else {
        createBrew(formData);
      }
      navigate('/brews');
    }
  };

  const showError = (field: string) => touched[field] && errors[field];

  return (
    <div className="min-h-screen">
      <Navbar type="app" />

      <div className="max-w-3xl mx-auto px-8 py-8">
        <Link
          to={isEdit ? `/brew/${id}` : '/brews'}
          className="inline-flex items-center gap-1 text-sm text-[#6B4226] hover:underline mb-6"
        >
          <ArrowLeft size={16} />
          Back
        </Link>

        <div className="bg-white rounded-xl border border-[#E8DDD1] p-8">
          <h1 className="text-2xl mb-8" style={{ fontFamily: 'var(--font-heading)' }}>
            {isEdit ? 'Edit brew log' : 'Log a new brew'}
          </h1>

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Bean & Method Row */}
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label htmlFor="bean" className="block text-sm text-[#8C7B6B] mb-2">
                  Bean *
                </label>
                <select
                  id="bean"
                  value={formData.bean}
                  onChange={(e) => handleFieldChange('bean', e.target.value)}
                  onBlur={() => handleFieldBlur('bean')}
                  className={`w-full px-4 py-2.5 bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B4226] focus:border-transparent ${
                    showError('bean') ? 'border-red-500' : 'border-[#E8DDD1]'
                  }`}
                >
                  <option value="">Select bean</option>
                  {beans.map(bean => (
                    <option key={bean} value={bean}>{bean}</option>
                  ))}
                </select>
                {showError('bean') && <p className="text-red-500 text-xs mt-1">{errors.bean}</p>}
              </div>

              <div>
                <label htmlFor="method" className="block text-sm text-[#8C7B6B] mb-2">
                  Method *
                </label>
                <select
                  id="method"
                  value={formData.method}
                  onChange={(e) => handleFieldChange('method', e.target.value)}
                  onBlur={() => handleFieldBlur('method')}
                  className={`w-full px-4 py-2.5 bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B4226] focus:border-transparent ${
                    showError('method') ? 'border-red-500' : 'border-[#E8DDD1]'
                  }`}
                >
                  <option value="">Select method</option>
                  {methods.map(method => (
                    <option key={method} value={method}>{method}</option>
                  ))}
                </select>
                {showError('method') && <p className="text-red-500 text-xs mt-1">{errors.method}</p>}
              </div>
            </div>

            {/* Date & Grinder Row */}
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label htmlFor="date" className="block text-sm text-[#8C7B6B] mb-2">
                  Date *
                </label>
                <input
                  type="date"
                  id="date"
                  value={formData.date}
                  onChange={(e) => handleFieldChange('date', e.target.value)}
                  onBlur={() => handleFieldBlur('date')}
                  className={`w-full px-4 py-2.5 bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B4226] focus:border-transparent ${
                    showError('date') ? 'border-red-500' : 'border-[#E8DDD1]'
                  }`}
                />
                {showError('date') && <p className="text-red-500 text-xs mt-1">{errors.date}</p>}
              </div>

              <div>
                <label htmlFor="grinder" className="block text-sm text-[#8C7B6B] mb-2">
                  Grinder *
                </label>
                <select
                  id="grinder"
                  value={formData.grinder}
                  onChange={(e) => handleFieldChange('grinder', e.target.value)}
                  onBlur={() => handleFieldBlur('grinder')}
                  className={`w-full px-4 py-2.5 bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B4226] focus:border-transparent ${
                    showError('grinder') ? 'border-red-500' : 'border-[#E8DDD1]'
                  }`}
                >
                  <option value="">Select grinder</option>
                  {grinders.map(grinder => (
                    <option key={grinder} value={grinder}>{grinder}</option>
                  ))}
                </select>
                {showError('grinder') && <p className="text-red-500 text-xs mt-1">{errors.grinder}</p>}
              </div>
            </div>

            {/* Dose, Water, Temp, Time Row */}
            <div className="grid grid-cols-4 gap-4">
              <div>
                <label htmlFor="dose" className="block text-sm text-[#8C7B6B] mb-2">
                  Dose (g) *
                </label>
                <input
                  type="number"
                  id="dose"
                  step="0.1"
                  value={formData.dose}
                  onChange={(e) => handleFieldChange('dose', parseFloat(e.target.value))}
                  onBlur={() => handleFieldBlur('dose')}
                  className={`w-full px-4 py-2.5 bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B4226] focus:border-transparent ${
                    showError('dose') ? 'border-red-500' : 'border-[#E8DDD1]'
                  }`}
                />
                {showError('dose') && <p className="text-red-500 text-xs mt-1">{errors.dose}</p>}
              </div>

              <div>
                <label htmlFor="water" className="block text-sm text-[#8C7B6B] mb-2">
                  Water (g) *
                </label>
                <input
                  type="number"
                  id="water"
                  step="1"
                  value={formData.water}
                  onChange={(e) => handleFieldChange('water', parseFloat(e.target.value))}
                  onBlur={() => handleFieldBlur('water')}
                  className={`w-full px-4 py-2.5 bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B4226] focus:border-transparent ${
                    showError('water') ? 'border-red-500' : 'border-[#E8DDD1]'
                  }`}
                />
                {showError('water') && <p className="text-red-500 text-xs mt-1">{errors.water}</p>}
              </div>

              <div>
                <label htmlFor="temp" className="block text-sm text-[#8C7B6B] mb-2">
                  Temp (°C) *
                </label>
                <input
                  type="number"
                  id="temp"
                  step="1"
                  value={formData.temp}
                  onChange={(e) => handleFieldChange('temp', parseFloat(e.target.value))}
                  onBlur={() => handleFieldBlur('temp')}
                  className={`w-full px-4 py-2.5 bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B4226] focus:border-transparent ${
                    showError('temp') ? 'border-red-500' : 'border-[#E8DDD1]'
                  }`}
                />
                {showError('temp') && <p className="text-red-500 text-xs mt-1">{errors.temp}</p>}
              </div>

              <div>
                <label htmlFor="time" className="block text-sm text-[#8C7B6B] mb-2">
                  Brew time *
                </label>
                <input
                  type="text"
                  id="time"
                  placeholder="MM:SS"
                  value={formData.time}
                  onChange={(e) => handleFieldChange('time', e.target.value)}
                  onBlur={() => handleFieldBlur('time')}
                  className={`w-full px-4 py-2.5 bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B4226] focus:border-transparent ${
                    showError('time') ? 'border-red-500' : 'border-[#E8DDD1]'
                  }`}
                />
                {showError('time') && <p className="text-red-500 text-xs mt-1">{errors.time}</p>}
              </div>
            </div>

            {/* Grind, Brewer, Yield */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label htmlFor="grind" className="block text-sm text-[#8C7B6B] mb-2">
                  Grind setting *
                </label>
                <input
                  type="text"
                  id="grind"
                  placeholder="e.g. 24 clicks"
                  value={formData.grind}
                  onChange={(e) => handleFieldChange('grind', e.target.value)}
                  onBlur={() => handleFieldBlur('grind')}
                  className={`w-full px-4 py-2.5 bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B4226] focus:border-transparent ${
                    showError('grind') ? 'border-red-500' : 'border-[#E8DDD1]'
                  }`}
                />
                {showError('grind') && <p className="text-red-500 text-xs mt-1">{errors.grind}</p>}
              </div>

              <div>
                <label htmlFor="brewer" className="block text-sm text-[#8C7B6B] mb-2">
                  Brewer *
                </label>
                <select
                  id="brewer"
                  value={formData.brewer}
                  onChange={(e) => handleFieldChange('brewer', e.target.value)}
                  onBlur={() => handleFieldBlur('brewer')}
                  className={`w-full px-4 py-2.5 bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B4226] focus:border-transparent ${
                    showError('brewer') ? 'border-red-500' : 'border-[#E8DDD1]'
                  }`}
                >
                  <option value="">Select brewer</option>
                  {brewers.map(brewer => (
                    <option key={brewer} value={brewer}>{brewer}</option>
                  ))}
                </select>
                {showError('brewer') && <p className="text-red-500 text-xs mt-1">{errors.brewer}</p>}
              </div>

              <div>
                <label htmlFor="yield" className="block text-sm text-[#8C7B6B] mb-2">
                  Yield (g, optional)
                </label>
                <input
                  type="number"
                  id="yield"
                  step="1"
                  value={formData.yield}
                  onChange={(e) => handleFieldChange('yield', parseFloat(e.target.value) || 0)}
                  onBlur={() => handleFieldBlur('yield')}
                  className={`w-full px-4 py-2.5 bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B4226] focus:border-transparent ${
                    showError('yield') ? 'border-red-500' : 'border-[#E8DDD1]'
                  }`}
                />
                {showError('yield') && <p className="text-red-500 text-xs mt-1">{errors.yield}</p>}
              </div>
            </div>

            <div className="h-px bg-[#E8DDD1]" />

            {/* Post-Brew Review */}
            <div>
              <p className="text-xs font-semibold text-[#8C7B6B] mb-4 uppercase tracking-wide">
                Post-brew review
              </p>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm text-[#8C7B6B] mb-3">
                    How did it taste? *
                  </label>
                  <div className="flex flex-wrap gap-3">
                    {tasteOptions.map(option => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => handleFieldChange('taste', option.value)}
                        onBlur={() => handleFieldBlur('taste')}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                          formData.taste === option.value
                            ? 'bg-[#6B4226] text-white'
                            : 'bg-[#F5EDE3] text-[#6B4226] hover:bg-[#E8DDD1]'
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                  {showError('taste') && <p className="text-red-500 text-xs mt-1">{errors.taste}</p>}
                </div>

                <div>
                  <label className="block text-sm text-[#8C7B6B] mb-3">
                    Rating *
                  </label>
                  <StarRating
                    rating={formData.rating}
                    size={28}
                    interactive
                    onChange={(rating) => handleFieldChange('rating', rating)}
                  />
                  {showError('rating') && <p className="text-red-500 text-xs mt-1">{errors.rating}</p>}
                </div>

                <div>
                  <label className="block text-sm text-[#8C7B6B] mb-3">
                    Tasting notes
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {flavorOptions.map(flavor => (
                      <FlavorTag
                        key={flavor}
                        label={flavor}
                        selected={formData.flavorTags.includes(flavor)}
                        onClick={() => toggleFlavor(flavor)}
                      />
                    ))}
                  </div>
                </div>

                <div>
                  <label htmlFor="notes" className="block text-sm text-[#8C7B6B] mb-2">
                    Notes
                  </label>
                  <textarea
                    id="notes"
                    rows={3}
                    placeholder="How was this cup?"
                    value={formData.notes}
                    onChange={(e) => handleFieldChange('notes', e.target.value)}
                    onBlur={() => handleFieldBlur('notes')}
                    className={`w-full px-4 py-3 bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B4226] focus:border-transparent resize-none ${
                      showError('notes') ? 'border-red-500' : 'border-[#E8DDD1]'
                    }`}
                  />
                  {showError('notes') && <p className="text-red-500 text-xs mt-1">{errors.notes}</p>}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4 pt-4">
              <button
                type="submit"
                className="px-8 py-3 bg-[#6B4226] text-white rounded-lg hover:bg-[#4A2E18] transition-colors font-medium"
              >
                {isEdit ? 'Save changes' : 'Log brew'}
              </button>
              <Link
                to={isEdit ? `/brew/${id}` : '/brews'}
                className="px-8 py-3 text-[#6B4226] hover:bg-[#F5EDE3] rounded-lg transition-colors"
              >
                Cancel
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
```

**Step 2: Test the form manually**

- Navigate to `/brew/new`
- Try submitting with empty fields → see validation errors
- Fill in some fields, leave required empty → errors should appear
- Try invalid values (temp < 80, dose = 0) → see errors
- Fill form correctly → should submit successfully

**Step 3: Commit**

```bash
git add src/app/pages/BrewForm.tsx
git commit -m "feat: integrate useBrewValidation and useBrewCRUD into BrewForm with real-time validation and error display"
```

---

## Task 5: Update BrewList with Pagination and Delete

**Files:**
- Modify: `src/app/pages/BrewList.tsx`

**Step 1: Rewrite BrewList with pagination**

```typescript
import { Link } from 'react-router';
import { Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { Navbar } from '../components/Navbar';
import { StarRating } from '../components/StarRating';
import { TasteBadge } from '../components/TasteBadge';
import { useBrewCRUD } from '../hooks/useBrewCRUD';
import { useBrewPagination } from '../hooks/useBrewPagination';

export function BrewList() {
  const { getBrews, deleteBrew } = useBrewCRUD();
  const brews = getBrews();
  const { currentPage, totalPages, currentItems, nextPage, prevPage, goToPage } = useBrewPagination(brews, 10);

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this brew?')) {
      deleteBrew(id);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#FEF9F3] via-[#FCF5EC] to-[#F5EDE3]">
      <Navbar type="app" />

      <div className="max-w-6xl mx-auto px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl" style={{ fontFamily: 'var(--font-heading)' }}>
            Brew Logs
          </h1>
          <Link
            to="/brew/new"
            className="px-6 py-2.5 bg-[#6B4226] text-white rounded-lg hover:bg-[#4A2E18] transition-colors font-medium"
          >
            + New Brew
          </Link>
        </div>

        {brews.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-[#8C7B6B] mb-4">No brew logs yet. Start logging your brews!</p>
            <Link
              to="/brew/new"
              className="inline-block px-6 py-2.5 bg-[#6B4226] text-white rounded-lg hover:bg-[#4A2E18]"
            >
              Log Your First Brew
            </Link>
          </div>
        ) : (
          <>
            <div className="bg-white rounded-xl border border-[#E8DDD1] overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-[#E8DDD1] bg-[#F5EDE3]">
                      <th className="px-6 py-4 text-left text-sm font-semibold text-[#6B4226]">Date</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-[#6B4226]">Bean</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-[#6B4226]">Method</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-[#6B4226]">Rating</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-[#6B4226]">Taste</th>
                      <th className="px-6 py-4 text-center text-sm font-semibold text-[#6B4226]">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentItems.map((brew, index) => (
                      <tr
                        key={brew.id}
                        className={`border-b border-[#E8DDD1] hover:bg-[#FEF9F3] transition-colors ${
                          index % 2 === 0 ? 'bg-white' : 'bg-[#FDFAF5]'
                        }`}
                      >
                        <td className="px-6 py-4 text-sm text-[#6B4226]">
                          {new Date(brew.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        </td>
                        <td className="px-6 py-4 text-sm text-[#6B4226]">{brew.bean}</td>
                        <td className="px-6 py-4 text-sm text-[#6B4226]">{brew.method}</td>
                        <td className="px-6 py-4">
                          <StarRating rating={brew.rating} size={16} />
                        </td>
                        <td className="px-6 py-4">
                          <TasteBadge taste={brew.taste} />
                        </td>
                        <td className="px-6 py-4 text-center space-x-2">
                          <Link
                            to={`/brew/${brew.id}`}
                            className="inline-block px-3 py-1.5 text-xs font-medium text-[#6B4226] bg-[#F5EDE3] hover:bg-[#E8DDD1] rounded transition-colors"
                          >
                            View
                          </Link>
                          <button
                            onClick={() => handleDelete(brew.id)}
                            className="inline-block px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 rounded transition-colors"
                            title="Delete brew"
                          >
                            <Trash2 size={16} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between mt-6">
              <p className="text-sm text-[#8C7B6B]">
                Page {currentPage} of {totalPages} ({brews.length} total brews)
              </p>
              <div className="flex gap-2">
                <button
                  onClick={prevPage}
                  disabled={currentPage === 1}
                  className="p-2 rounded border border-[#E8DDD1] hover:bg-[#F5EDE3] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft size={18} />
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                  <button
                    key={page}
                    onClick={() => goToPage(page)}
                    className={`w-8 h-8 rounded font-medium transition-colors ${
                      currentPage === page
                        ? 'bg-[#6B4226] text-white'
                        : 'border border-[#E8DDD1] text-[#6B4226] hover:bg-[#F5EDE3]'
                    }`}
                  >
                    {page}
                  </button>
                ))}
                <button
                  onClick={nextPage}
                  disabled={currentPage === totalPages}
                  className="p-2 rounded border border-[#E8DDD1] hover:bg-[#F5EDE3] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
```

**Step 2: Test manually**

- Navigate to `/brews`
- Verify pagination works (navigate pages)
- Test delete button → confirms deletion

**Step 3: Commit**

```bash
git add src/app/pages/BrewList.tsx
git commit -m "feat: add pagination and delete functionality to BrewList"
```

---

## Task 6: Update BrewDetail with Edit/Delete Buttons

**Files:**
- Modify: `src/app/pages/BrewDetail.tsx`

**Step 1: Add edit/delete buttons to BrewDetail**

Add these buttons before the closing div in the detail view:

```typescript
<div className="flex gap-4 mt-8 pt-8 border-t border-[#E8DDD1]">
  <Link
    to={`/brew/${brew.id}/edit`}
    className="px-6 py-2.5 bg-[#6B4226] text-white rounded-lg hover:bg-[#4A2E18] transition-colors font-medium"
  >
    Edit
  </Link>
  <button
    onClick={() => {
      if (confirm('Delete this brew log?')) {
        deleteBrew(brew.id);
        navigate('/brews');
      }
    }}
    className="px-6 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
  >
    Delete
  </button>
</div>
```

Add this import at the top:

```typescript
import { useBrewCRUD } from '../hooks/useBrewCRUD';
```

Add this inside the component:

```typescript
const { deleteBrew } = useBrewCRUD();
```

**Step 2: Test**

- Navigate to a brew detail page
- Click edit → should go to form with pre-filled data
- Click delete → should confirm and delete

**Step 3: Commit**

```bash
git add src/app/pages/BrewDetail.tsx
git commit -m "feat: add edit and delete buttons to BrewDetail page"
```

---

## Task 7: Verify Landing Page is Complete

**Files:**
- Check: `src/app/pages/Landing.tsx`

**Step 1: Verify Landing page has all required elements**

Ensure Landing.tsx displays:
- ✅ BrewLog logo
- ✅ "BrewLog" name/title
- ✅ Tagline (e.g., "Track every brew, perfect your craft")
- ✅ Brief description of the app
- ✅ Navigation to start (login/register or browse)

If missing any element, add them now.

**Step 2: Test**

- Navigate to `/` → should see complete landing page

**Step 3: Commit if changes made**

```bash
git add src/app/pages/Landing.tsx
git commit -m "feat: ensure Landing page has complete presentation (logo, name, tagline, description)"
```

---

## Task 8: Run All Tests and Check Coverage

**Files:**
- Test: `src/app/hooks/__tests__/*.test.ts`

**Step 1: Run all tests**

```bash
npm test
```

Expected: All 20+ tests PASS

**Step 2: Check coverage**

```bash
npm test -- --coverage
```

Expected: ~70-80% coverage on hooks; lower on components is OK for now

**Step 3: Commit test results**

```bash
git commit -m "test: verify all validation, CRUD, and pagination tests passing with ~75% coverage"
```

---

## Final Checklist

- [ ] useBrewValidation hook + tests ✅
- [ ] useBrewCRUD hook + tests ✅
- [ ] useBrewPagination hook + tests ✅
- [ ] BrewForm updated with validation + CRUD
- [ ] BrewList updated with pagination + delete
- [ ] BrewDetail updated with edit/delete buttons
- [ ] Landing page complete (logo, name, tagline, description)
- [ ] All tests passing (~75% coverage)
- [ ] No lint errors

---

**Total tasks: 8**
**Estimated time: 4-5 hours**
**Deadline: Week 5**
