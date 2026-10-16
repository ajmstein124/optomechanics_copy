%% Optical band structure of snowflake unit cell -- diamond at 619 nm
% Adapted from Bdagger_unitcell_OP_band_Gap.m (Si, 1562 nm).
%
% Changes from original:
%   filename: unit_cell_2 -> unit_cell_3  (unit_cell_3 contains both mech and optical physics)
%   a    : 478 nm  -> 190 nm   (same a/lambda = 0.306 at lambda=619 nm)
%   d    : 162 nm  -> 64 nm    (same d/a = 0.339)
%   w    : 93 nm   -> 37 nm    (same w/a = 0.195)
%   f_r  : 25 nm   -> 10 nm    (same f_r/a = 0.052)
%   t    : 220 nm  -> 140 nm   (diamond slab, user specified)
%   t_air: unchanged (1.5 um, set in model)
%   f0   : 150 THz -> 400 THz  (search center below 484.7 THz = 619 nm)
%   sweep ranges scaled by a_diamond/a_Si = 0.396
%   Material overrides: Silicon props -> Diamond (E=1050 GPa, nu=0.07, rho=3500, eps_r=5.81)
%
% Target optical frequency: 484.7 THz (619 nm, SnV ZPL)

frog_folder = '';
filename = 'unit_cell_3';
model = mphload([frog_folder filename]);
save_folder = [frog_folder 'simu_data\diamond_optical\'];
mkdir(save_folder);

%% Parameters
a = 190e-9;
d_sweep = linspace(-8e-9, 8e-9, 11);
w_sweep = linspace(-4e-9, 4e-9, 11);
ds = 64e-9 + d_sweep;
ws = 37e-9 + w_sweep;
t = 140e-9;

[dm, wm] = meshgrid(ds, ws);
comb = [dm(:), wm(:)];

N_freqs = 12;
f0 = 400e12;   % search center below 484.7 THz (619 nm)

%% Set diamond material properties (override Silicon built-in)
model.material('mat1').propertyGroup('def').set('density',       '3500[kg/m^3]');
model.material('mat1').propertyGroup('def').set('youngsmodulus', '1050e9[Pa]');
model.material('mat1').propertyGroup('def').set('poissonsratio', '0.07');
% n=2.41 -> eps_r = n^2 = 5.81
model.material('mat1').propertyGroup('def').set('relpermittivity', ...
    {'5.81', '0', '0', '0', '5.81', '0', '0', '0', '5.81'});

for ic = 1:size(comb, 1)
    d = comb(ic, 1);
    w = comb(ic, 2);
    model.param.set('a',      num2str(a));
    model.param.set('d',      num2str(d));
    model.param.set('w',      num2str(w));
    model.param.set('f_r',    '10e-9');
    model.param.set('t',      num2str(t));
    model.param.set('N_mode', num2str(N_freqs));
    model.param.set('f_op',   num2str(f0));

    N_ks = 5;

    kxs_GM = pi/a*linspace(0, 1,   N_ks);
    kys_GM = pi/a*linspace(0, 1/sqrt(3), N_ks);
    kxs_MK = pi/a*linspace(1, 4/3, N_ks);
    kys_MK = pi/a*linspace(1/sqrt(3), 0, N_ks);
    kxs_KG = pi/a*linspace(4/3, 0, N_ks);
    kys_KG = pi/a*linspace(0, 0,  N_ks);

    kxs = [kxs_GM, kxs_MK(2:end), kxs_KG(2:end)];
    kys = [kys_GM, kys_MK(2:end), kys_KG(2:end)];
    ks  = [kxs; kys];

    freqs = zeros(length(ks), 2*N_freqs);

    for ii = 1:length(ks)
        tic
        disp(['Computing ' num2str(ii) ' out of ' num2str(length(ks)) ...
              ', kx = ' num2str(ks(1,ii)) ', ky = ' num2str(ks(2,ii)) ...
              ', d = ' num2str(d) ', w = ' num2str(w)]);
        model.param.set('kFx', num2str(ks(1,ii)));
        model.param.set('kFy', num2str(ks(2,ii)));

        % PMC (TE-like modes)
        model.component('comp1').physics('ewfd').feature('pec2').active(false);
        model.component('comp1').physics('ewfd').feature('pmc1').active(true);
        model.sol('sol2').runAll;
        freqs(ii, 1:end/2) = mphglobal(model, 'freq', 'Dataset', 'dset2');

        % PEC (TM-like modes)
        model.component('comp1').physics('ewfd').feature('pmc1').active(false);
        model.component('comp1').physics('ewfd').feature('pec2').active(true);
        model.sol('sol2').runAll;
        freqs(ii, end/2+1:end) = mphglobal(model, 'freq', 'Dataset', 'dset2');

        fname = [save_folder sprintf('diamond_OP_bands_d_%gnm_w_%gnm_ii_%s.mat', ...
                 d*1e9, w*1e9, num2str(ii))];
        save(fname, 'freqs', 'ks', 'a', 'd', 'w', 't', 'f0', 'N_ks');
        toc
    end

    %% Plot bands
    figure(); hold on;
    for jj = 1:size(freqs, 1)
        plot(jj, 1e-12*real(freqs(jj, 1:end/2)),    'b.');
        plot(jj, 1e-12*real(freqs(jj, end/2+1:end)), 'r.');
    end
    yline(484.7e12 * 1e-12, 'k--', '619 nm');   % target wavelength marker
    ylabel('Frequency (THz)')
    set(gca, 'fontsize', 12)
    xticks([1, N_ks, 2*N_ks-1, 3*N_ks-2]);
    xticklabels({'\Gamma', 'M', 'K', '\Gamma'});
    xlim([1, 3*N_ks-2])
    legend('PMC (TE-like)', 'PEC (TM-like)')
    title(sprintf('Diamond optical, a=190nm, d=%.0fnm, w=%.0fnm, t=140nm', d*1e9, w*1e9))
    saveas(gcf, [save_folder sprintf('diamond_OP_band_d_%gnm_w_%gnm.jpg', d*1e9, w*1e9)]);
end
