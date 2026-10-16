%% test_comsol_license.m
% Quick sanity check: verifies COMSOL LiveLink license and basic solver.
% Run this manually in MATLAB on the Windows machine (open MATLAB, paste path, run).
% Does NOT require unit_cell_3.mph.
%
% Expected output:
%   COMSOL version: <version string>
%   Model created OK
%   Geometry built OK
%   Mesh built OK
%   Eigenfrequencies (Hz): <two numbers near 0>
%   COMSOL LiveLink: ALL CHECKS PASSED

disp('--- COMSOL LiveLink license test ---');

%% 1. Start COMSOL server
disp('Starting COMSOL server (mphstart)...');
mphstart;
disp(['COMSOL version: ' mphversion]);

%% 2. Create a trivial model: elastic block, find eigenfrequencies
disp('Creating model...');
model = ModelUtil.create('TestModel');
model.component.create('comp1', true);
model.component('comp1').geom.create('geom1', 3);
disp('Model created OK');

%% 3. Build geometry: simple unit cube (1 um)
model.component('comp1').geom('geom1').create('blk1', 'Block');
model.component('comp1').geom('geom1').feature('blk1').set('size', {'1e-6', '1e-6', '1e-6'});
model.component('comp1').geom('geom1').run;
disp('Geometry built OK');

%% 4. Add material (silicon, built-in)
model.component('comp1').material.create('mat1', 'Common');
model.component('comp1').material('mat1').selection.all;
model.component('comp1').material('mat1').propertyGroup('def').set('density',       '2329[kg/m^3]');
model.component('comp1').material('mat1').propertyGroup('def').set('youngsmodulus', '170e9[Pa]');
model.component('comp1').material('mat1').propertyGroup('def').set('poissonsratio', '0.28');

%% 5. Add solid mechanics physics, free (no BCs needed for eigenfrequency)
model.component('comp1').physics.create('solid', 'SolidMechanics', 'geom1');

%% 6. Mesh
model.component('comp1').mesh.create('mesh1', 'geom1');
model.component('comp1').mesh('mesh1').autoMeshSize(5);   % coarse
model.component('comp1').mesh('mesh1').run;
disp('Mesh built OK');

%% 7. Eigenfrequency study
model.study.create('std1');
model.study('std1').create('eig', 'Eigenfrequency');
model.study('std1').feature('eig').set('neigs', 2);
model.study('std1').feature('eig').set('shift', '1e6');   % 1 MHz shift

model.sol.create('sol1');
model.sol('sol1').study('std1');
model.sol('sol1').attach('std1');
model.sol('sol1').runAll;

%% 8. Extract result
freqs = mphglobal(model, 'solid.freq', 'Dataset', 'dset1');
disp(['Eigenfrequencies (Hz): ' num2str(real(freqs(:))', '%.3e  ')]);

disp('COMSOL LiveLink: ALL CHECKS PASSED');

ModelUtil.remove('TestModel');
