import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { getField, OverviewCards } from './OverviewCards';
import type { StateBatchResponse } from '../../api/types';

const sampleState: StateBatchResponse = {
  'Agent.Core.status': {
    _meta: { type: 'state', module: 'Agent', component: 'Core', source_file: 'pacli_status.log', name: 'status' },
    data: { state: 'Enabled', mode: 'Always On', epm_status: 'Up', local_hostname: 'TEST-HOST', username: 'user@example.com' },
  },
  'Agent.Core.version': {
    _meta: { type: 'state', module: 'Agent', component: 'Core', source_file: 'pacli_version.log', name: 'version' },
    data: { version: '26.1.2.4' },
  },
  'Agent.Core.sw_vers': {
    _meta: { type: 'state', module: 'Agent', component: 'Core', source_file: 'sw_vers.txt', name: 'sw_vers' },
    data: { productname: 'macOS', productversion: '26.2' },
  },
  'System.Core.uname': {
    _meta: { type: 'state', module: 'System', component: 'Core', source_file: 'uname.txt', name: 'uname' },
    data: { kernel: 'Darwin TEST-HOST 25.2.0 Darwin Kernel Version 25.2.0 arm64', architecture: 'arm64' },
  },
};

describe('getField — null-safe state data traversal', () => {
  it('returns field value from nested state data', () => {
    expect(getField(sampleState, 'Agent.Core.status', 'state')).toBe('Enabled');
  });

  it('returns N/A when key is missing', () => {
    expect(getField(sampleState, 'Agent.Core.nonexistent', 'state')).toBe('N/A');
  });

  it('returns N/A when field is missing', () => {
    expect(getField(sampleState, 'Agent.Core.status', 'nonexistent_field')).toBe('N/A');
  });

  it('returns N/A when stateData is undefined', () => {
    expect(getField(undefined, 'Agent.Core.status', 'state')).toBe('N/A');
  });

  it('converts non-string values to string', () => {
    const data: StateBatchResponse = {
      'test.key': {
        _meta: { type: 'state', module: 'Test', component: 'Core', source_file: 'test', name: 'test' },
        data: { count: 42 },
      },
    };
    expect(getField(data, 'test.key', 'count')).toBe('42');
  });
});

describe('OverviewCards — rendering', () => {
  it('shows loading spinner when loading', () => {
    render(<OverviewCards stateData={undefined} loading={true} />);
    // Antd Spin renders with role="img" or a specific class
    expect(document.querySelector('.ant-spin')).not.toBeNull();
  });

  it('renders agent version from state data', () => {
    render(<OverviewCards stateData={sampleState} loading={false} />);
    expect(screen.getByText('26.1.2.4')).toBeInTheDocument();
  });

  it('renders hostname from state data', () => {
    render(<OverviewCards stateData={sampleState} loading={false} />);
    expect(screen.getByText('TEST-HOST')).toBeInTheDocument();
  });

  it('shows N/A for missing fields without crashing', () => {
    const sparseState: StateBatchResponse = {
      'Agent.Core.status': {
        _meta: { type: 'state', module: 'Agent', component: 'Core', source_file: '', name: 'status' },
        data: {},
      },
    };
    // Should not throw
    render(<OverviewCards stateData={sparseState} loading={false} />);
    // Multiple N/A values should appear
    const naElements = screen.getAllByText('N/A');
    expect(naElements.length).toBeGreaterThan(0);
  });
});
