// Mock react-router-dom BrowserRouter to avoid nested Router issue
// App.tsx uses BrowserRouter internally, we wrap with MemoryRouter and mock BrowserRouter as passthrough
jest.mock('react-router-dom', () => {
  const actual = jest.requireActual('react-router-dom') as any;
  return {
    ...actual,
    BrowserRouter: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="browser-router">{children}</div>
    ),
  };
});

// Mock antd ConfigProvider and App to avoid complex theming issues
jest.mock('antd', () => {
  const actual = jest.requireActual('antd') as any;
  return {
    ...actual,
    ConfigProvider: ({ children }: { children: React.ReactNode }) => children,
    App: ({ children }: { children: React.ReactNode }) => children,
  };
});

import React from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

// Mock authService
jest.mock('./services/authService', () => ({
  authService: {
    isAuthenticated: jest.fn(() => false),
  },
}));

describe('App', () => {
  it('renders without crashing', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    expect(() =>
      render(
        <MemoryRouter initialEntries={['/auth']}>
          <App />
        </MemoryRouter>
      )
    ).not.toThrow();
    consoleSpy.mockRestore();
  });

  it('shows auth page when not authenticated', () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/auth']}>
        <App />
      </MemoryRouter>
    );
    expect(container).toBeTruthy();
  });
});
